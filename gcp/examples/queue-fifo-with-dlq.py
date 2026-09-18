"""カード queue-fifo-with-dlq: 順序保証と配信不能トピック付きの購読を組み立てる純粋関数。

Pub/Sub の `create_topic` / `create_subscription` に渡す設定を返す。API は呼ばない。
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

# 配信不能トピックへ送るまでの試行回数
MIN_DELIVERY_ATTEMPTS = 5
MAX_DELIVERY_ATTEMPTS = 100
# 確認応答の期限
MIN_ACK_SECONDS = 10
MAX_ACK_SECONDS = 600


def ordered_subscription_with_dlq(
    topic: str,
    subscription: str,
    dead_letter_topic: str,
    *,
    ack_deadline_seconds: int = 60,
    max_delivery_attempts: int = 5,
    message_retention_days: int = 7,
    enable_exactly_once: bool = True,
    filter_expression: str | None = None,
) -> dict:
    """順序を保ち、失敗したメッセージを退避する購読の設定を返す。

    Args:
        topic: 購読元トピックの完全名
        subscription: 購読の完全名
        dead_letter_topic: 配信不能トピックの完全名
        ack_deadline_seconds: 確認応答の期限。10〜600
        max_delivery_attempts: 退避までの試行回数。5〜100
        message_retention_days: 未確認メッセージを保持する日数。1〜7
        enable_exactly_once: 一度だけの配信を有効にするか
        filter_expression: 購読側で絞り込む式

    Returns:
        topic_config と subscription_config を持つ dict

    Raises:
        ValueError: 名前の形式違い、配信不能トピックが購読元と同じ、
            確認応答の期限や試行回数や保持日数が範囲外の場合
    """
    _check_resource("topic", "topic", topic)
    _check_resource("subscription", "subscription", subscription)
    _check_resource("dead_letter_topic", "topic", dead_letter_topic)
    if dead_letter_topic == topic:
        raise ValueError("配信不能トピックを購読元と同じにすると失敗が循環する")
    if not MIN_ACK_SECONDS <= ack_deadline_seconds <= MAX_ACK_SECONDS:
        raise ValueError(
            f"確認応答の期限は {MIN_ACK_SECONDS}〜{MAX_ACK_SECONDS} 秒: {ack_deadline_seconds}"
        )
    if not MIN_DELIVERY_ATTEMPTS <= max_delivery_attempts <= MAX_DELIVERY_ATTEMPTS:
        raise ValueError(
            f"試行回数は {MIN_DELIVERY_ATTEMPTS}〜{MAX_DELIVERY_ATTEMPTS}: {max_delivery_attempts}"
        )
    if not 1 <= message_retention_days <= 7:
        raise ValueError(f"保持日数は 1〜7: {message_retention_days}")

    subscription_config: dict = {
        "name": subscription,
        "topic": topic,
        "ack_deadline_seconds": ack_deadline_seconds,
        "message_retention_duration": {"seconds": message_retention_days * 86400},
        # 順序指定キーごとに順番を保つ
        "enable_message_ordering": True,
        "enable_exactly_once_delivery": enable_exactly_once,
        "retain_acked_messages": False,
        "dead_letter_policy": {
            "dead_letter_topic": dead_letter_topic,
            "max_delivery_attempts": max_delivery_attempts,
        },
        "retry_policy": {
            "minimum_backoff": {"seconds": 10},
            "maximum_backoff": {"seconds": 600},
        },
    }
    if filter_expression is not None:
        subscription_config["filter"] = filter_expression

    return {
        "topic_config": {"name": topic, "message_retention_duration": {"seconds": 86400}},
        "subscription_config": subscription_config,
    }
