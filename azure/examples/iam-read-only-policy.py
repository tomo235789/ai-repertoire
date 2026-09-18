"""カード iam-read-only-policy: 読み取りだけを許すロール定義を組み立てる純粋関数。

`azure-mgmt-authorization` の `role_definitions.create_or_update` に渡す
RoleDefinition と、組み込み Reader ロールの ID を返す。API は呼ばない。
"""

from __future__ import annotations

import re
import uuid

# 組み込み Reader ロール（テナントに依らず固定）
BUILT_IN_READER_ROLE_ID = "acdd72a7-3385-48ef-bd42-f606fba81ae7"

_PROVIDER_RE = re.compile(r"^Microsoft\.[A-Za-z0-9]+$")
_SCOPE_RE = re.compile(r"^/subscriptions/([^/]+)(/.*)?$")
_ROLE_NAMESPACE = uuid.UUID("6ba7b813-9dad-11d1-80b4-00c04fd430c8")

# `/read` の形をしているのに秘密値そのものを返すため、読み取り専用から外す操作
SECRET_REVEALING_ACTIONS = (
    "Microsoft.KeyVault/vaults/secrets/read",
    "Microsoft.KeyVault/vaults/keys/read",
)
# notActions は管理プレーンにしか効かないので、データプレーンの側は入力時に弾く
SECRET_REVEALING_DATA_ACTIONS = (
    "Microsoft.KeyVault/vaults/secrets/getSecret/action",
    "Microsoft.KeyVault/vaults/keys/read",
    "Microsoft.KeyVault/vaults/secrets/readMetadata/action",
)


def read_only_role(
    role_name: str,
    providers: tuple[str, ...] | list[str],
    assignable_scopes: tuple[str, ...] | list[str],
    *,
    description: str = "読み取り専用",
    data_read_actions: tuple[str, ...] | list[str] = (),
) -> dict:
    """指定したプロバイダの読み取り操作だけを許すロール定義を返す。

    Args:
        role_name: ロールの表示名
        providers: 対象のリソースプロバイダ。例 ("Microsoft.Storage",)
        assignable_scopes: ロールを割り当てられるスコープ。1 件以上
        description: ロールの説明
        data_read_actions: データプレーンの読み取り操作。明示したときだけ含める

    Returns:
        role_definition_id と role_definition を持つ dict

    Raises:
        ValueError: providers か assignable_scopes が空、プロバイダ名やスコープの形式違い、
            書き込み系の操作や秘密を読める操作を data_read_actions に混ぜた場合
    """
    providers = tuple(providers)
    assignable_scopes = tuple(assignable_scopes)
    data_read_actions = tuple(data_read_actions)

    if not providers:
        raise ValueError("providers は 1 件以上必要")
    if not assignable_scopes:
        raise ValueError("assignable_scopes は 1 件以上必要")
    for provider in providers:
        if not _PROVIDER_RE.match(provider):
            raise ValueError(f"プロバイダ名の形式が不正: {provider!r}")
    for scope in assignable_scopes:
        if not _SCOPE_RE.match(scope):
            raise ValueError(f"スコープの形式が不正: {scope!r}")
    for action in data_read_actions:
        if not action.endswith("/read"):
            raise ValueError(f"データプレーンにも読み取り以外は入れられない: {action!r}")
        if action.startswith("Microsoft.KeyVault/") or action in SECRET_REVEALING_DATA_ACTIONS:
            raise ValueError(
                f"秘密そのものを読める操作は読み取り専用に入れられない: {action!r}"
            )

    actions = sorted(f"{provider}/*/read" for provider in providers)
    role_definition_id = str(
        uuid.uuid5(_ROLE_NAMESPACE, f"{role_name}|{assignable_scopes[0]}")
    )

    return {
        "role_definition_id": role_definition_id,
        "role_definition": {
            "roleName": role_name,
            "description": description,
            "type": "CustomRole",
            "permissions": [
                {
                    "actions": actions,
                    "notActions": list(SECRET_REVEALING_ACTIONS),
                    "dataActions": sorted(data_read_actions),
                    "notDataActions": [],
                }
            ],
            "assignableScopes": list(assignable_scopes),
        },
    }


def built_in_reader_role_id(scope: str) -> str:
    """組み込み Reader ロールの定義 ID を、スコープのサブスクリプション配下で返す。

    Raises:
        ValueError: scope が /subscriptions/ から始まらない場合
    """
    match = _SCOPE_RE.match(scope)
    if match is None:
        raise ValueError(f"スコープの形式が不正: {scope!r}")
    # ロール定義はサブスクリプションスコープに置かれる
    return (
        f"/subscriptions/{match.group(1)}"
        f"/providers/Microsoft.Authorization/roleDefinitions/{BUILT_IN_READER_ROLE_ID}"
    )
