"""カード queue-fanout-topic: 1 つのイベントを複数の購読者へ配る構成を組み立てる純粋関数。

Pub/Sub のトピックと購読の設定を返す。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9._~+%-]{2,254}$")
_PATH_RE = {
    "topic": re.compile(r"^projects/[^/]+/topics/(.+)$"),
    "subscription": re.compile(r"^projects/[^/]+/subscriptions/(.+)$"),
}


def _check_resource(label: str, kind: str, value: str) -> None:
    """projects/<project>/<種別>/<id> の形と、末尾の ID の形式を見る"""
    match = _PATH_RE[kind].match(value)
    if match is None:
        raise ValueError(
            f"{label} は projects/<project>/{kind}s/<id> の完全名で指定する: {value!r}"
        )
    if not _NAME_RE.match(match.group(1)):
        raise ValueError(f"{label} の名前の形式が不正: {value!r}")
_HTTPS_RE = re.compile(r"^https://[^\s]+$")


def fanout_topic(
    topic: str,
    subscribers: dict[str, dict],
    *,
    message_retention_days: int = 1,
    schema: str | None = None,
    kms_key_name: str | None = None,
) -> dict:
    """1 つのトピックと、購読者ごとの購読設定を返す。

    Args:
        topic: トピックの完全名
        subscribers: 購読の完全名 -> 設定。設定のキーは
            filter（絞り込み式）、push_endpoint（プッシュ配信先の HTTPS URL）、
            push_service_account（プッシュ時に署名するサービスアカウント）
        message_retention_days: トピック側でメッセージを保持する日数。1〜31
        schema: メッセージスキーマの完全名
        kms_key_name: メッセージを暗号化する鍵の完全名

    Returns:
        topic_config と subscription_configs（購読名順のリスト）を持つ dict

    Raises:
        ValueError: 名前の形式違い、購読者が空、保持日数が範囲外、
            未知の設定キー、プッシュ配信先が HTTPS でない、
            プッシュなのにサービスアカウントが無い場合
    """
    _check_resource("topic", "topic", topic)
    if not subscribers:
        raise ValueError("subscribers は 1 件以上必要")
    if not 1 <= message_retention_days <= 31:
        raise ValueError(f"保持日数は 1〜31: {message_retention_days}")

    topic_config: dict = {
        "name": topic,
        "message_retention_duration": {"seconds": message_retention_days * 86400},
    }
    if schema is not None:
        topic_config["schema_settings"] = {"schema": schema, "encoding": "JSON"}
    if kms_key_name is not None:
        topic_config["kms_key_name"] = kms_key_name

    subscription_configs: list[dict] = []
    for name, options in sorted(subscribers.items()):
        _check_resource("subscription", "subscription", name)
        unknown = set(options) - {"filter", "push_endpoint", "push_service_account"}
        if unknown:
            raise ValueError(f"未知の設定キー: {sorted(unknown)}")

        config: dict = {
            "name": name,
            "topic": topic,
            "ack_deadline_seconds": 60,
            "expiration_policy": {},  # 空にすると購読が自動で消えない
        }
        if "filter" in options:
            config["filter"] = options["filter"]
        if "push_endpoint" in options:
            endpoint = options["push_endpoint"]
            if not _HTTPS_RE.match(endpoint):
                raise ValueError(f"プッシュ配信先は HTTPS にする: {endpoint!r}")
            service_account = options.get("push_service_account")
            if not service_account:
                raise ValueError(
                    f"プッシュ配信には署名するサービスアカウントが要る: {name!r}"
                )
            config["push_config"] = {
                "push_endpoint": endpoint,
                "oidc_token": {"service_account_email": service_account},
            }
        subscription_configs.append(config)

    return {"topic_config": topic_config, "subscription_configs": subscription_configs}
