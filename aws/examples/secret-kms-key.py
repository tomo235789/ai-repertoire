"""カード secret-kms-key: 顧客管理の対称鍵（CMK）を管理者と利用者を分けたキーポリシー付きで作る

kms.create_key / create_alias / enable_key_rotation / schedule_key_deletion の kwargs を返す。
KeyId は create_key の応答で決まるため、後続の kwargs には KEY_ID_PLACEHOLDER を入れてある。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

KEY_ID_PLACEHOLDER = "{KeyId}"

_ALIAS_RE = re.compile(r"^alias/(?!aws/)[A-Za-z0-9/_-]{1,250}$")
_ACCOUNT_RE = re.compile(r"^\d{12}$")
_IAM_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:iam::\d{12}:(?:root|user/|role/)")

MIN_PENDING_WINDOW_DAYS = 7
MAX_PENDING_WINDOW_DAYS = 30

# 鍵の管理（ポリシー変更・削除予約など）。暗号化・復号は含めない
ADMIN_ACTIONS = [
    "kms:Create*",
    "kms:Describe*",
    "kms:Enable*",
    "kms:List*",
    "kms:Put*",
    "kms:Update*",
    "kms:Revoke*",
    "kms:Disable*",
    "kms:Get*",
    "kms:Delete*",
    "kms:TagResource",
    "kms:UntagResource",
    "kms:ScheduleKeyDeletion",
    "kms:CancelKeyDeletion",
]
# 鍵の利用（暗号化・復号・データキー生成）。ポリシー変更や削除は含めない
USER_ACTIONS = [
    "kms:Encrypt",
    "kms:Decrypt",
    "kms:ReEncrypt*",
    "kms:GenerateDataKey*",
    "kms:DescribeKey",
]
# AWS サービス（RDS / SQS など）が鍵を使うために必要なグラント操作
GRANT_ACTIONS = ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"]


def _check_arns(arns: Sequence[str], label: str) -> list[str]:
    items = list(arns)
    if len(set(items)) != len(items):
        raise ValueError(f"{label} に重複がある")
    for arn in items:
        if "*" in arn or not _IAM_ARN_RE.match(arn):
            raise ValueError(f"{label}: IAM プリンシパルの ARN ではない（ワイルドカード不可）: {arn!r}")
    return items


def customer_managed_key(
    alias: str,
    admin_principal_arns: Sequence[str],
    user_principal_arns: Sequence[str],
    account_id: str,
    pending_window_days: int = MAX_PENDING_WINDOW_DAYS,
    *,
    root_full_access: bool = True,
    description: str | None = None,
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """対称 CMK の作成・エイリアス・自動ローテーション・削除予約の kwargs をまとめて返す。

    :param alias: `alias/` で始まるエイリアス名（`alias/aws/` は予約で不可）
    :param admin_principal_arns: 鍵を管理する（削除予約・ポリシー変更）IAM プリンシパル
    :param user_principal_arns: 鍵で暗号化・復号する IAM プリンシパル
    :param account_id: 鍵を置くアカウント（12 桁）
    :param pending_window_days: 削除予約から実削除までの猶予（7〜30 日）
    :param root_full_access: True ならアカウントルートに kms:* を与える（IAM ポリシーでの権限付与が可能になる）。
        False にするなら admin_principal_arns が必須（さもないと管理不能な鍵になる）
    """
    if not _ALIAS_RE.match(alias):
        raise ValueError(f"エイリアスは alias/ で始まり alias/aws/ 以外にする: {alias!r}")
    if not _ACCOUNT_RE.match(account_id):
        raise ValueError(f"account_id は 12 桁の数字: {account_id!r}")
    if isinstance(pending_window_days, bool) or not isinstance(pending_window_days, int):
        raise TypeError("pending_window_days は int")
    if not MIN_PENDING_WINDOW_DAYS <= pending_window_days <= MAX_PENDING_WINDOW_DAYS:
        raise ValueError(
            f"pending_window_days は {MIN_PENDING_WINDOW_DAYS}〜{MAX_PENDING_WINDOW_DAYS}（実際: {pending_window_days}）"
        )
    admins = _check_arns(admin_principal_arns, "admin_principal_arns")
    users = _check_arns(user_principal_arns, "user_principal_arns")
    if not root_full_access and not admins:
        raise ValueError("root_full_access=False のときは admin_principal_arns が必須（管理不能な鍵になる）")

    statements: list[dict[str, Any]] = []
    if root_full_access:
        statements.append(
            {
                "Sid": "EnableRootAccountAccess",
                "Effect": "Allow",
                "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                "Action": "kms:*",
                "Resource": "*",
            }
        )
    if admins:
        statements.append(
            {
                "Sid": "AllowKeyAdministration",
                "Effect": "Allow",
                "Principal": {"AWS": admins},
                "Action": list(ADMIN_ACTIONS),
                "Resource": "*",
            }
        )
    if users:
        statements.append(
            {
                "Sid": "AllowKeyUsage",
                "Effect": "Allow",
                "Principal": {"AWS": users},
                "Action": list(USER_ACTIONS),
                "Resource": "*",
            }
        )
        statements.append(
            {
                "Sid": "AllowGrantsForAwsResources",
                "Effect": "Allow",
                "Principal": {"AWS": users},
                "Action": list(GRANT_ACTIONS),
                "Resource": "*",
                "Condition": {"Bool": {"kms:GrantIsForAWSResource": "true"}},
            }
        )

    create_key: dict[str, Any] = {
        "KeyUsage": "ENCRYPT_DECRYPT",
        "KeySpec": "SYMMETRIC_DEFAULT",
        "Origin": "AWS_KMS",
        "MultiRegion": False,
        "BypassPolicyLockoutSafetyCheck": False,
        "Policy": {"Version": "2012-10-17", "Id": f"key-policy-{alias.removeprefix('alias/')}", "Statement": statements},
    }
    if description:
        create_key["Description"] = description
    if tags:
        create_key["Tags"] = [{"TagKey": k, "TagValue": v} for k, v in sorted(tags.items())]

    return {
        "create_key": create_key,
        "create_alias": {"AliasName": alias, "TargetKeyId": KEY_ID_PLACEHOLDER},
        "enable_key_rotation": {"KeyId": KEY_ID_PLACEHOLDER, "RotationPeriodInDays": 365},
        "schedule_key_deletion": {"KeyId": KEY_ID_PLACEHOLDER, "PendingWindowInDays": pending_window_days},
    }
