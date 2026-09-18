"""カード iam-cross-account-trust: 別アカウントからのロール引き受けを許可する信頼関係を組み立てる純粋関数。

create_role の AssumeRolePolicyDocument と MaxSessionDuration を返す。API は呼ばない。
"""

from __future__ import annotations

import re
from typing import Any, Iterable

MIN_SESSION_SECONDS = 3600
MAX_SESSION_SECONDS = 43200
_ACCOUNT_ID_RE = re.compile(r"^\d{12}$")
# sts:ExternalId に使える文字と長さ（2〜1224）
_EXTERNAL_ID_RE = re.compile(r"^[\w+=,.@:/-]{2,1224}$", re.ASCII)


def _normalize_account_ids(account_ids: Iterable[str]) -> list[str]:
    result = sorted(set(account_ids))
    if not result:
        raise ValueError("account_ids must not be empty")
    for account_id in result:
        if not _ACCOUNT_ID_RE.match(account_id):
            raise ValueError(f"account id must be 12 digits: {account_id!r}")
    return result


def cross_account_trust(
    account_ids: Iterable[str],
    external_id: str,
    max_session_seconds: int = MIN_SESSION_SECONDS,
    require_mfa: bool = False,
) -> dict[str, Any]:
    """指定アカウントに ExternalId 付きでロールの引き受けを許可する設定を返す。

    返り値:
      assume_role_policy   : create_role の AssumeRolePolicyDocument（dict。json.dumps して渡す）
      max_session_duration : create_role / update_role の MaxSessionDuration（秒）

    信頼ポリシー側にも sts:DurationSeconds の上限を入れるので、引き受け側が
    max_session_seconds より長いセッションを要求すると拒否される。
    """
    accounts = _normalize_account_ids(account_ids)
    if not _EXTERNAL_ID_RE.match(external_id):
        raise ValueError("external_id must be 2-1224 chars of [A-Za-z0-9_+=,.@:/-]")
    if (
        isinstance(max_session_seconds, bool)
        or not isinstance(max_session_seconds, int)
        or not MIN_SESSION_SECONDS <= max_session_seconds <= MAX_SESSION_SECONDS
    ):
        raise ValueError(
            f"max_session_seconds must be between {MIN_SESSION_SECONDS} and {MAX_SESSION_SECONDS}: {max_session_seconds!r}"
        )

    condition: dict[str, Any] = {
        "StringEquals": {"sts:ExternalId": external_id},
        "NumericLessThanEqualsIfExists": {"sts:DurationSeconds": str(max_session_seconds)},
    }
    if require_mfa:
        condition["Bool"] = {"aws:MultiFactorAuthPresent": "true"}

    return {
        "assume_role_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "CrossAccountAssumeRole",
                    "Effect": "Allow",
                    "Principal": {"AWS": [f"arn:aws:iam::{a}:root" for a in accounts]},
                    "Action": "sts:AssumeRole",
                    "Condition": condition,
                }
            ],
        },
        "max_session_duration": max_session_seconds,
    }
