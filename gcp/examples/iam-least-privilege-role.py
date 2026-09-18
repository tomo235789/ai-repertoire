"""カード iam-least-privilege-role: 必要な権限だけを集めたカスタムロールを組み立てる純粋関数。

IAM の `projects.roles.create` に渡す roleId と Role を返す。API は呼ばない。
"""

from __future__ import annotations

import re

_ROLE_ID_RE = re.compile(r"^[a-zA-Z0-9_.]{3,64}$")
_PERMISSION_RE = re.compile(r"^[a-z][a-zA-Z0-9]*\.[a-zA-Z0-9.]+\.[a-zA-Z]+$")

_STAGES = ("ALPHA", "BETA", "GA", "DEPRECATED", "DISABLED")

# 付けると他のロールを自由に足せる、または他の ID になりすませる権限。
# 個別の名前だけでは取りこぼすので、動詞の側でも捕まえる
PRIVILEGE_ESCALATING_PERMISSIONS = frozenset(
    {
        "iam.roles.create",
        "iam.roles.update",
        "iam.serviceAccounts.actAs",
        "iam.serviceAccounts.getAccessToken",
        "iam.serviceAccounts.getOpenIdToken",
        "iam.serviceAccounts.implicitDelegation",
        "iam.serviceAccounts.signBlob",
        "iam.serviceAccounts.signJwt",
        "iam.serviceAccountKeys.create",
        "deploymentmanager.deployments.create",
    }
)
# 末尾がこれらの権限は、対象が何であれ IAM を書き換えられる
_ESCALATING_SUFFIXES = (".setIamPolicy",)


def least_privilege_role(
    role_id: str,
    title: str,
    permissions: tuple[str, ...] | list[str],
    *,
    description: str = "",
    stage: str = "GA",
    allow_privilege_escalation: bool = False,
) -> dict:
    """指定した権限だけを持つカスタムロールを返す。

    Args:
        role_id: ロール ID。英数字とアンダースコアとピリオドで 3〜64 文字
        title: 一覧に出る名前
        permissions: 含める権限。1 件以上
        description: 説明
        stage: 公開ステージ。_STAGES のいずれか
        allow_privilege_escalation: 権限昇格につながる権限を明示的に許す

    Returns:
        role_id と role を持つ dict

    Raises:
        ValueError: ロール ID や権限の形式違い、権限が空、未知のステージ、
            権限昇格につながる権限を明示許可なしに含めた場合
    """
    if not _ROLE_ID_RE.match(role_id):
        raise ValueError(f"ロール ID の形式が不正: {role_id!r}")
    if not title:
        raise ValueError("title は空にできない")
    if stage not in _STAGES:
        raise ValueError(f"ステージは {_STAGES} のいずれか: {stage!r}")

    unique = sorted(set(permissions))
    if not unique:
        raise ValueError("permissions は 1 件以上必要")
    for permission in unique:
        if "*" in permission:
            raise ValueError(f"権限にワイルドカードは使えない: {permission!r}")
        if not _PERMISSION_RE.match(permission):
            raise ValueError(f"権限の形式が不正: {permission!r}")

    escalating = sorted(
        permission
        for permission in unique
        if permission in PRIVILEGE_ESCALATING_PERMISSIONS
        or permission.endswith(_ESCALATING_SUFFIXES)
    )
    if escalating and not allow_privilege_escalation:
        raise ValueError(
            f"権限昇格につながる権限が含まれる: {escalating}。"
            "必要なら allow_privilege_escalation=True を明示する"
        )

    return {
        "role_id": role_id,
        "role": {
            "title": title,
            "description": description,
            "includedPermissions": unique,
            "stage": stage,
        },
    }
