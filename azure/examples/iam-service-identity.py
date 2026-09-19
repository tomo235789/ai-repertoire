"""カード iam-service-identity: ワークロード用のマネージド ID にロールを割り当てる純粋関数。

`azure-mgmt-authorization` の `role_assignments.create` と、リソース側の `identity`
プロパティに渡す dict を組み立てる。API は呼ばず、資格情報も環境変数も読まない。
"""

from __future__ import annotations

import re
import uuid

# Azure の組み込みロール定義 ID（テナントに依らず固定の GUID）
BUILT_IN_ROLES: dict[str, str] = {
    "Reader": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
    "Contributor": "b24988ac-6180-42a0-ab88-20f7382dd24c",
    "Owner": "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
    "User Access Administrator": "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9",
    "Storage Blob Data Reader": "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
    "Storage Blob Data Contributor": "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
    "Key Vault Secrets User": "4633458b-17de-408a-b874-0445c86b69e6",
    "Monitoring Metrics Publisher": "3913510d-42f4-4e42-8a64-420c390055eb",
}

# ワークロードの ID に渡すと権限昇格ができてしまうロール
PRIVILEGE_ESCALATING_ROLES = frozenset({"Owner", "User Access Administrator"})

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
_SCOPE_RE = re.compile(r"^/subscriptions/([^/\r\n]+)(/.*)?$")
_UAMI_RE = re.compile(
    r"^/subscriptions/[^/\r\n]+/resourceGroups/[^/\r\n]+"
    r"/providers/Microsoft\.ManagedIdentity/userAssignedIdentities/[^/\r\n]+$"
)

# ロール割り当て名を入力から決めるための固定名前空間（呼び出しごとに変わらない）
_ASSIGNMENT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def service_identity_config(
    principal_id: str,
    scope: str,
    *,
    role_name: str = "Reader",
    user_assigned_identity_id: str | None = None,
    allow_privileged_role: bool = False,
) -> dict:
    """マネージド ID にロールを割り当てるための設定を返す。

    `user_assigned_identity_id` を渡すとユーザー割り当て ID、省略するとシステム割り当て
    ID の `identity` ブロックを返す。

    Args:
        principal_id: マネージド ID のオブジェクト ID（GUID）
        scope: 割り当て先スコープ。/subscriptions/... で始まる ARM ID
        role_name: 組み込みロール名。BUILT_IN_ROLES のキー
        user_assigned_identity_id: ユーザー割り当て ID の ARM リソース ID
        allow_privileged_role: Owner / User Access Administrator を明示的に許可する

    Returns:
        identity（リソースに付ける ID ブロック）と assignment（ロール割り当て）を持つ dict

    Raises:
        ValueError: principal_id が GUID でない、scope の形式が違う、未知のロール名、
            ユーザー割り当て ID が ARM リソース ID でない、
            権限昇格ロールを明示許可なしに指定した場合
    """
    if not _UUID_RE.fullmatch(principal_id):
        raise ValueError(f"principal_id は GUID を指定する: {principal_id!r}")
    if not _SCOPE_RE.fullmatch(scope):
        raise ValueError(f"scope は /subscriptions/ から始まる ARM ID を指定する: {scope!r}")
    if role_name not in BUILT_IN_ROLES:
        raise ValueError(f"未知の組み込みロール: {role_name!r}")
    if role_name in PRIVILEGE_ESCALATING_ROLES and not allow_privileged_role:
        raise ValueError(
            f"{role_name} はワークロードの ID に割り当てない。"
            "必要なら allow_privileged_role=True を明示する"
        )

    if user_assigned_identity_id is not None and not _UAMI_RE.fullmatch(user_assigned_identity_id):
        raise ValueError(
            "ユーザー割り当て ID は Microsoft.ManagedIdentity の ARM リソース ID を指定する: "
            f"{user_assigned_identity_id!r}"
        )

    if user_assigned_identity_id is None:
        identity: dict = {"type": "SystemAssigned"}
    else:
        identity = {
            "type": "UserAssigned",
            "userAssignedIdentities": {user_assigned_identity_id: {}},
        }

    # ロール定義はサブスクリプションスコープに置かれる。
    # 割り当て先がリソースグループでも、定義 ID は /subscriptions/<id> から作る
    subscription_scope = f"/subscriptions/{_SCOPE_RE.fullmatch(scope).group(1)}"
    role_definition_id = (
        f"{subscription_scope}/providers/Microsoft.Authorization/roleDefinitions/"
        f"{BUILT_IN_ROLES[role_name]}"
    )
    # 同じ入力なら同じ名前になるよう、入力から決定的に導く（uuid4 は使わない）
    assignment_name = str(
        uuid.uuid5(_ASSIGNMENT_NAMESPACE, f"{scope}|{principal_id}|{role_name}")
    )

    return {
        "identity": identity,
        "assignment": {
            "scope": scope,
            "role_assignment_name": assignment_name,
            "parameters": {
                "properties": {
                    "roleDefinitionId": role_definition_id,
                    "principalId": principal_id,
                    "principalType": "ServicePrincipal",
                }
            },
        },
        "role_name": role_name,
    }
