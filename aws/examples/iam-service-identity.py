"""カード iam-service-identity: ワークロード用のサービス ID（AWS サービスまたは OIDC）にロールを引き受けさせる信頼ポリシーを組み立てる純粋関数。

create_role の AssumeRolePolicyDocument（dict）を返す。API は呼ばない。
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

PRINCIPAL_KINDS = ("service", "oidc")
_OIDC_MARKER = ":oidc-provider/"


def _values(value: str | Sequence[str]) -> str | list[str]:
    if isinstance(value, str):
        if not value:
            raise ValueError("condition value must not be empty")
        return value
    items = sorted(set(value))
    if not items or any(not v for v in items):
        raise ValueError("condition values must be non-empty strings")
    return items


def _has_wildcard(value: str | list[str]) -> bool:
    items = [value] if isinstance(value, str) else value
    return any("*" in v or "?" in v for v in items)


def _add_condition(condition: dict[str, dict[str, Any]], operator: str, key: str, value: Any) -> None:
    condition.setdefault(operator, {})[key] = value


def _oidc_statement(principal: str, conditions: Mapping[str, str | Sequence[str]]) -> dict[str, Any]:
    if not principal.startswith("arn:") or _OIDC_MARKER not in principal:
        raise ValueError(f"oidc principal must be an OIDC provider ARN: {principal!r}")
    host = principal.split(_OIDC_MARKER, 1)[1]
    if not host:
        raise ValueError(f"oidc provider ARN has no host: {principal!r}")

    normalized = {(k if ":" in k else f"{host}:{k}"): _values(v) for k, v in conditions.items()}
    for required in (f"{host}:sub", f"{host}:aud"):
        if required not in normalized:
            raise ValueError(f"oidc trust requires condition {required!r}")
    if _has_wildcard(normalized[f"{host}:aud"]):
        raise ValueError("aud condition must be an exact value")

    condition: dict[str, dict[str, Any]] = {}
    for key in sorted(normalized):
        value = normalized[key]
        _add_condition(condition, "StringLike" if _has_wildcard(value) else "StringEquals", key, value)
    return {
        "Effect": "Allow",
        "Principal": {"Federated": principal},
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": condition,
    }


def _service_statement(principal: str, conditions: Mapping[str, str | Sequence[str]]) -> dict[str, Any]:
    if not principal.endswith(".amazonaws.com") or principal.startswith("."):
        raise ValueError(f"service principal must be like lambda.amazonaws.com: {principal!r}")
    statement: dict[str, Any] = {
        "Effect": "Allow",
        "Principal": {"Service": principal},
        "Action": "sts:AssumeRole",
    }
    if conditions:
        condition: dict[str, dict[str, Any]] = {}
        for key in sorted(conditions):
            if not key.startswith("aws:"):
                raise ValueError(f"service trust conditions must be aws:* keys (aws:SourceAccount, aws:SourceArn): {key!r}")
            value = _values(conditions[key])
            if not _has_wildcard(value):
                operator = "StringEquals"
            elif key == "aws:SourceArn":
                operator = "ArnLike"
            else:
                operator = "StringLike"
            _add_condition(condition, operator, key, value)
        statement["Condition"] = condition
    return statement


def service_identity_trust(
    principal_kind: str,
    principal: str,
    conditions: Mapping[str, str | Sequence[str]] | None = None,
) -> dict[str, Any]:
    """ワークロードにロールを引き受けさせる信頼ポリシーを返す。

    principal_kind = "service": principal は "lambda.amazonaws.com" などのサービスプリンシパル。
        conditions は aws:SourceAccount / aws:SourceArn（任意。混乱した代理の防止に推奨）
    principal_kind = "oidc": principal は OIDC プロバイダの ARN
        （arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com）。
        conditions に sub と aud が必須。キーは "sub" でも "<host>:sub" でもよい
    """
    conditions = conditions or {}
    if principal_kind == "oidc":
        statement = _oidc_statement(principal, conditions)
    elif principal_kind == "service":
        statement = _service_statement(principal, conditions)
    else:
        raise ValueError(f"principal_kind must be one of {PRINCIPAL_KINDS}: {principal_kind!r}")
    return {"Version": "2012-10-17", "Statement": [statement]}
