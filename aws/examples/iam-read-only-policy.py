"""カード iam-read-only-policy: 読み取り専用の IAM ポリシー文書を組み立てる純粋関数。

create_policy / put_role_policy の PolicyDocument（dict）を返す。API は呼ばない。
"""

from __future__ import annotations

import re
from typing import Any, Iterable

# "<service>:Get|List|Describe..."。末尾の * だけ許す（s3:Get* など）
_READ_ACTION_RE = re.compile(r"^[a-z0-9-]+:(Get|List|Describe)[A-Za-z0-9]*\*?$")

# 名前は Get* だが秘密値や一時資格情報を返すため、読み取り専用ポリシーからは除外する action
SECRET_REVEALING_ACTIONS = frozenset(
    {
        "secretsmanager:GetSecretValue",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "sts:GetFederationToken",
        "sts:GetSessionToken",
    }
)


def _normalize_actions(actions: Iterable[str]) -> list[str]:
    result = sorted(set(actions))
    if not result:
        raise ValueError("actions must not be empty")
    for action in result:
        if not _READ_ACTION_RE.match(action):
            raise ValueError(f"only Get*/List*/Describe* actions are allowed: {action!r}")
        if action in SECRET_REVEALING_ACTIONS:
            raise ValueError(f"action reveals secrets and is not read-only: {action!r}")
    return result


def _normalize_resources(resources: Iterable[str]) -> list[str]:
    result = sorted(set(resources))
    if not result:
        raise ValueError("resources must not be empty")
    for resource in result:
        if resource != "*" and not resource.startswith("arn:"):
            raise ValueError(f"resource must be an ARN or '*': {resource!r}")
    return result


def read_only_policy(actions: Iterable[str], resources: Iterable[str]) -> dict[str, Any]:
    """Get* / List* / Describe* だけを許可するポリシー文書を返す。

    Describe* / List* 系の action はリソースレベルの制限に対応しないものが多いので、
    resources には "*" も渡せる。
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ReadOnly",
                "Effect": "Allow",
                "Action": _normalize_actions(actions),
                "Resource": _normalize_resources(resources),
            }
        ],
    }
