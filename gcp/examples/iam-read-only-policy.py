"""カード iam-read-only-policy: 読み取りだけを許す IAM ポリシーを組み立てる純粋関数。

`set_iam_policy` に渡す Policy（bindings を持つ dict）を返す。API は呼ばない。
"""

from __future__ import annotations

import re

_ROLE_RE = re.compile(r"^(roles/[a-zA-Z0-9.]+|projects/[^/]+/roles/[a-zA-Z0-9_.]+)$")
_MEMBER_RE = re.compile(
    r"^(user|serviceAccount|group|domain|principalSet|principal):[^\s]+$"
)

# 名前は viewer でも実データや設定を読めてしまう、読み取り専用に含めないロール
OVERBROAD_VIEWER_ROLES = frozenset(
    {"roles/editor", "roles/owner", "roles/iam.securityAdmin", "roles/iam.serviceAccountTokenCreator"}
)
# 誰でも当てはまる特別なメンバー
PUBLIC_MEMBERS = frozenset({"allUsers", "allAuthenticatedUsers"})


def read_only_policy(
    bindings: dict[str, tuple[str, ...] | list[str]],
    *,
    etag: str | None = None,
    condition_expression: str | None = None,
    condition_title: str = "",
) -> dict:
    """読み取り系のロールだけを含むポリシーを返す。

    Args:
        bindings: ロール -> メンバーの一覧
        etag: 読み込んだポリシーの etag。同時更新の取り違えを防ぐ
        condition_expression: 全バインディングに付ける CEL 条件
        condition_title: 条件の名前。条件を付けるときは必須

    Returns:
        version 3 の Policy dict

    Raises:
        ValueError: バインディングが空、ロールやメンバーの形式違い、
            allUsers などの公開メンバー、書き込みできる広いロール、
            条件式と名前が揃っていない場合
    """
    if not bindings:
        raise ValueError("bindings は 1 件以上必要")
    if (condition_expression is None) != (not condition_title):
        raise ValueError("条件には式と名前の両方が要る")

    condition = (
        {"title": condition_title, "expression": condition_expression}
        if condition_expression is not None
        else None
    )

    result: list[dict] = []
    for role, members in sorted(bindings.items()):
        if not _ROLE_RE.match(role):
            raise ValueError(f"ロールの形式が不正: {role!r}")
        if role in OVERBROAD_VIEWER_ROLES:
            raise ValueError(f"読み取り専用に含められないロール: {role!r}")
        if role.startswith("roles/") and not (
            role.endswith("Viewer") or role.endswith("viewer") or ".get" in role
        ):
            raise ValueError(f"事前定義ロールは閲覧者ロールだけ許す: {role!r}")
        unique_members = sorted(set(members))
        if not unique_members:
            raise ValueError(f"メンバーが空: {role!r}")
        for member in unique_members:
            if member in PUBLIC_MEMBERS:
                raise ValueError(f"公開メンバーには付与しない: {member!r}")
            if not _MEMBER_RE.match(member):
                raise ValueError(f"メンバーの形式が不正: {member!r}")
        binding: dict = {"role": role, "members": unique_members}
        if condition is not None:
            binding["condition"] = dict(condition)
        result.append(binding)

    policy: dict = {"version": 3, "bindings": result}
    if etag is not None:
        policy["etag"] = etag
    return policy
