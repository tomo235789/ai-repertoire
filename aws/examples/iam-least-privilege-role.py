"""カード iam-least-privilege-role: 特定の操作だけを許可する IAM ロールの設定を組み立てる純粋関数。

create_role / put_role_policy に渡す信頼ポリシーと権限ポリシー（dict）を返す。API は呼ばない。
"""

from __future__ import annotations

import re
from typing import Any, Iterable

_ROLE_NAME_RE = re.compile(r"^[\w+=,.@-]{1,64}$", re.ASCII)
# "<service>:<Action>"。ワイルドカードは一切含めない
_ACTION_RE = re.compile(r"^[a-z0-9-]+:[A-Za-z0-9]+$")


def _validate_role_name(name: str) -> None:
    if not _ROLE_NAME_RE.match(name):
        raise ValueError(f"invalid role name: {name!r}")


def _validate_service(trusted_service: str) -> None:
    if not trusted_service.endswith(".amazonaws.com") or trusted_service.startswith("."):
        raise ValueError(f"trusted_service must be a service principal like lambda.amazonaws.com: {trusted_service!r}")


def _normalize_actions(actions: Iterable[str]) -> list[str]:
    result = sorted(set(actions))
    if not result:
        raise ValueError("actions must not be empty")
    for action in result:
        if not _ACTION_RE.match(action):
            raise ValueError(f"action must be '<service>:<Action>' without wildcards: {action!r}")
    return result


def _normalize_resources(resources: Iterable[str]) -> list[str]:
    result = sorted(set(resources))
    if not result:
        raise ValueError("resources must not be empty")
    for resource in result:
        if resource == "*" or not resource.startswith("arn:"):
            raise ValueError(f"resource must be an ARN, not a bare wildcard: {resource!r}")
    return result


def _validate_permissions_boundary(arn: str) -> None:
    if not arn.startswith("arn:") or ":policy/" not in arn:
        raise ValueError(f"permissions_boundary must be an IAM policy ARN: {arn!r}")


def least_privilege_role(
    name: str,
    trusted_service: str,
    actions: Iterable[str],
    resources: Iterable[str],
    permissions_boundary: str | None = None,
    source_account: str | None = None,
) -> dict[str, Any]:
    """指定した action と resource だけを許可するロールの設定を返す。

    返り値:
      role_name            : create_role の RoleName
      assume_role_policy   : create_role の AssumeRolePolicyDocument（dict。json.dumps して渡す）
      policy_name          : put_role_policy の PolicyName（"<name>-policy"）
      policy               : put_role_policy の PolicyDocument（dict。json.dumps して渡す）
      permissions_boundary : create_role の PermissionsBoundary（渡したときだけ）

    source_account を渡すと、信頼ポリシーに aws:SourceAccount の条件を付けて混乱した代理を防ぐ。
    """
    _validate_role_name(name)
    _validate_service(trusted_service)
    if source_account is not None and not re.fullmatch(r"\d{12}", source_account):
        raise ValueError(f"source_account must be a 12-digit account id: {source_account!r}")

    trust_statement: dict[str, Any] = {
        "Effect": "Allow",
        "Principal": {"Service": trusted_service},
        "Action": "sts:AssumeRole",
    }
    if source_account is not None:
        trust_statement["Condition"] = {"StringEquals": {"aws:SourceAccount": source_account}}

    config: dict[str, Any] = {
        "role_name": name,
        "assume_role_policy": {"Version": "2012-10-17", "Statement": [trust_statement]},
        "policy_name": f"{name}-policy",
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "LeastPrivilege",
                    "Effect": "Allow",
                    "Action": _normalize_actions(actions),
                    "Resource": _normalize_resources(resources),
                }
            ],
        },
    }
    if permissions_boundary is not None:
        _validate_permissions_boundary(permissions_boundary)
        config["permissions_boundary"] = permissions_boundary
    return config
