"""カード iam-service-identity: ワークロード用のサービスアカウントを組み立てる純粋関数。

サービスアカウントの作成リクエストと、プロジェクトへの IAM バインディング、
Workload Identity の紐付けを返す。API は呼ばず、鍵も作らない。
"""

from __future__ import annotations

import re

_ACCOUNT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_ROLE_RE = re.compile(r"^(roles/[a-zA-Z0-9.]+|projects/[^/]+/roles/[a-zA-Z0-9_.]+)$")

# ワークロードに付けると事実上の管理者になるロール
PRIVILEGED_ROLES = frozenset(
    {
        "roles/owner",
        "roles/editor",
        "roles/iam.securityAdmin",
        # ほかのサービスアカウントになりすませる、実質的な権限昇格
        "roles/iam.serviceAccountTokenCreator",
        "roles/iam.serviceAccountUser",
        "roles/resourcemanager.projectIamAdmin",
        "roles/resourcemanager.folderIamAdmin",
        "roles/resourcemanager.organizationAdmin",
        # 他のサービスアカウントを作り替えたり鍵を発行したりできる
        "roles/iam.serviceAccountAdmin",
        "roles/iam.serviceAccountKeyAdmin",
    }
)


def service_identity_config(
    project_id: str,
    account_id: str,
    roles: tuple[str, ...] | list[str],
    *,
    display_name: str = "",
    kubernetes_namespace: str | None = None,
    kubernetes_service_account: str | None = None,
    allow_privileged_roles: bool = False,
) -> dict:
    """サービスアカウントの作成と権限付与の設定を返す。

    Args:
        project_id: プロジェクト ID
        account_id: サービスアカウント ID。英小文字・数字・ハイフンで 6〜30 文字
        roles: 付与するロール。1 件以上
        display_name: 表示名。省略すると account_id を使う
        kubernetes_namespace: Workload Identity で紐付ける名前空間
        kubernetes_service_account: 紐付ける Kubernetes のサービスアカウント名
        allow_privileged_roles: owner / editor などを明示的に許す

    Returns:
        service_account / email / bindings / workload_identity_binding を持つ dict

    Raises:
        ValueError: ID やロールの形式違い、ロールが空、
            権限の広いロールを明示許可なしに指定、
            Workload Identity の指定が片方だけの場合
    """
    if not _PROJECT_RE.fullmatch(project_id):
        raise ValueError(f"プロジェクト ID の形式が不正: {project_id!r}")
    if not _ACCOUNT_ID_RE.fullmatch(account_id):
        raise ValueError(f"サービスアカウント ID は英小文字・数字・ハイフンで 6〜30 文字: {account_id!r}")
    unique_roles = sorted(set(roles))
    if not unique_roles:
        raise ValueError("roles は 1 件以上必要")
    for role in unique_roles:
        if not _ROLE_RE.fullmatch(role):
            raise ValueError(f"ロールの形式が不正: {role!r}")
    privileged = sorted(set(unique_roles) & PRIVILEGED_ROLES)
    if privileged and not allow_privileged_roles:
        raise ValueError(
            f"ワークロードに広すぎるロール: {privileged}。"
            "必要なら allow_privileged_roles=True を明示する"
        )
    if (kubernetes_namespace is None) != (kubernetes_service_account is None):
        raise ValueError("Workload Identity には名前空間とサービスアカウント名の両方が要る")
    if kubernetes_namespace is not None and not (
        kubernetes_namespace and kubernetes_service_account
    ):
        raise ValueError("Workload Identity の名前空間とサービスアカウント名は空にできない")

    email = f"{account_id}@{project_id}.iam.gserviceaccount.com"
    member = f"serviceAccount:{email}"

    workload_identity_binding = None
    if kubernetes_namespace is not None:
        workload_identity_binding = {
            "resource": f"projects/{project_id}/serviceAccounts/{email}",
            "role": "roles/iam.workloadIdentityUser",
            "members": [
                f"serviceAccount:{project_id}.svc.id.goog"
                f"[{kubernetes_namespace}/{kubernetes_service_account}]"
            ],
        }

    return {
        "service_account": {
            "accountId": account_id,
            "serviceAccount": {"displayName": display_name or account_id},
        },
        "email": email,
        "bindings": [{"role": role, "members": [member]} for role in unique_roles],
        "workload_identity_binding": workload_identity_binding,
    }
