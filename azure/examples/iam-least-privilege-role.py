"""カード iam-least-privilege-role: 特定の操作だけを許可するカスタムロールを組み立てる純粋関数。

`azure-mgmt-authorization` の `role_definitions.create_or_update` に渡す
RoleDefinition の properties を返す。API は呼ばない。
"""

from __future__ import annotations

import re
import uuid

_SCOPE_RE = re.compile(r"^/subscriptions/[^/]+(/.*)?$")
# 管理グループ配下のスコープも割り当て可能スコープになる
_MG_SCOPE_RE = re.compile(r"^/providers/Microsoft\.Management/managementGroups/[^/]+$")

# ロール定義名を入力から決めるための固定名前空間（呼び出しごとに変わらない）
_ROLE_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


# ロールや割り当てを書き換えられる操作。これを含むロールは自分で権限を増やせる
PRIVILEGE_ESCALATING_ACTIONS = (
    "Microsoft.Authorization/roleAssignments/write",
    "Microsoft.Authorization/roleAssignments/delete",
    "Microsoft.Authorization/roleDefinitions/write",
    "Microsoft.Authorization/roleDefinitions/delete",
    "Microsoft.Authorization/elevateAccess/action",
)


def _is_escalating(op: str) -> bool:
    """権限昇格につながる操作か、それを含むワイルドカードかを見る"""
    if op in PRIVILEGE_ESCALATING_ACTIONS:
        return True
    if not op.endswith("*"):
        return False
    prefix = op[:-1]
    return any(action.startswith(prefix) for action in PRIVILEGE_ESCALATING_ACTIONS)


def _check_operations(label: str, operations: tuple[str, ...]) -> None:
    for op in operations:
        if not op:
            raise ValueError(f"{label} に空文字は入れられない")
        if op == "*" or (op.endswith("/*") and op.count("/") == 1):
            # "*" やプロバイダ丸ごとの "Microsoft.Storage/*" は最小権限にならない
            raise ValueError(f"{label} に広すぎるワイルドカードは使えない: {op!r}")
        if _is_escalating(op):
            raise ValueError(
                f"{label} にロールを書き換えられる操作は入れられない: {op!r}。"
                "このロールを持つ相手が自分で権限を増やせる"
            )


def least_privilege_role(
    role_name: str,
    description: str,
    actions: tuple[str, ...] | list[str],
    assignable_scopes: tuple[str, ...] | list[str],
    *,
    data_actions: tuple[str, ...] | list[str] = (),
    not_actions: tuple[str, ...] | list[str] = (),
    not_data_actions: tuple[str, ...] | list[str] = (),
) -> dict:
    """許可する操作だけを並べたカスタムロール定義を返す。

    Args:
        role_name: ロールの表示名
        description: 何のためのロールかの説明
        actions: 許可する管理プレーンの操作。1 件以上
        assignable_scopes: このロールを割り当てられるスコープ。1 件以上
        data_actions: 許可するデータプレーンの操作
        not_actions: actions から除外する操作
        not_data_actions: data_actions から除外する操作

    Returns:
        role_definition_id（入力から決まる GUID）と role_definition（ARM の properties）を持つ dict

    Raises:
        ValueError: actions か assignable_scopes が空、スコープの形式違い、
            管理グループを 2 件以上指定、データプレーンの操作と管理グループの併用、
            `*` や `<Provider>/*` のような広すぎるワイルドカード、
            actions と not_actions に同じ操作が入っている場合
    """
    actions = tuple(actions)
    assignable_scopes = tuple(assignable_scopes)
    data_actions = tuple(data_actions)
    not_actions = tuple(not_actions)
    not_data_actions = tuple(not_data_actions)

    if not actions and not data_actions:
        raise ValueError("actions か data_actions のどちらかは 1 件以上必要")
    if not assignable_scopes:
        raise ValueError("assignable_scopes は 1 件以上必要")
    for scope in assignable_scopes:
        if not (_SCOPE_RE.fullmatch(scope) or _MG_SCOPE_RE.fullmatch(scope)):
            raise ValueError(f"割り当て可能スコープの形式が不正: {scope!r}")
    # カスタムロールに指定できる管理グループは 1 件まで
    management_groups = [s for s in assignable_scopes if _MG_SCOPE_RE.fullmatch(s)]
    if len(management_groups) > 1:
        raise ValueError("assignable_scopes に指定できる管理グループは 1 件まで")
    if management_groups and (data_actions or not_data_actions):
        raise ValueError(
            "データプレーンの操作を持つロールは、管理グループを割り当て可能スコープにできない"
        )

    _check_operations("actions", actions)
    _check_operations("dataActions", data_actions)

    overlap = set(actions) & set(not_actions)
    if overlap:
        raise ValueError(f"actions と not_actions が重複している: {sorted(overlap)}")
    data_overlap = set(data_actions) & set(not_data_actions)
    if data_overlap:
        raise ValueError(
            f"data_actions と not_data_actions が重複している: {sorted(data_overlap)}"
        )

    role_definition_id = str(uuid.uuid5(_ROLE_NAMESPACE, f"{role_name}|{assignable_scopes[0]}"))

    return {
        "role_definition_id": role_definition_id,
        "role_definition": {
            "roleName": role_name,
            "description": description,
            "type": "CustomRole",
            "permissions": [
                {
                    "actions": list(actions),
                    "notActions": list(not_actions),
                    "dataActions": list(data_actions),
                    "notDataActions": list(not_data_actions),
                }
            ],
            "assignableScopes": list(assignable_scopes),
        },
    }
