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


def _check_operations(label: str, operations: tuple[str, ...]) -> None:
    for op in operations:
        if not op:
            raise ValueError(f"{label} に空文字は入れられない")
        if op == "*" or op.endswith("/*") and op.count("/") == 1:
            # "*" やプロバイダ丸ごとの "Microsoft.Storage/*" は最小権限にならない
            raise ValueError(f"{label} に広すぎるワイルドカードは使えない: {op!r}")


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
        if not (_SCOPE_RE.match(scope) or _MG_SCOPE_RE.match(scope)):
            raise ValueError(f"割り当て可能スコープの形式が不正: {scope!r}")

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
