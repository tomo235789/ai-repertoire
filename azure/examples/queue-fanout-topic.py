"""カード queue-fanout-topic: 1 つのイベントを複数の購読者へ配る構成を組み立てる純粋関数。

`azure-mgmt-servicebus` の `topics.create_or_update` /
`subscriptions.create_or_update` / `rules.create_or_update` に渡す
プロパティを返す。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]{0,258}[A-Za-z0-9]$")
# サブスクリプション名はトピック名より短く、スラッシュを含められない
_SUBSCRIPTION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,48}[A-Za-z0-9]$|^[A-Za-z0-9]$")
# 重複検出の窓の上限は 7 日
MAX_DUPLICATE_DETECTION_DAYS = 7
# サブスクリプション作成時に自動で入る全通過ルールの名前
DEFAULT_RULE_NAME = "$Default"


def _iso_days(days: int) -> str:
    return f"P{days}D"


def fanout_topic(
    topic_name: str,
    subscribers: dict[str, str | None],
    *,
    message_ttl_days: int = 14,
    max_delivery_count: int = 5,
    duplicate_detection_days: int = 1,
) -> dict:
    """1 つのトピックと、購読者ごとのサブスクリプションとフィルタを返す。

    Args:
        topic_name: トピック名
        subscribers: サブスクリプション名 -> SQL フィルタ式。None なら全件受け取る
        message_ttl_days: メッセージの寿命
        max_delivery_count: この回数まで配信して駄目なら配信不能キューへ
        duplicate_detection_days: 重複検出の窓。0 で無効

    Returns:
        topic と subscriptions（名前をキーにした properties と rule）を持つ dict

    Raises:
        ValueError: 名前の形式違い、購読者が空、寿命や配信回数が不正、
            フィルタ式に危険な文字が混ざっている場合
    """
    if not _NAME_RE.match(topic_name):
        raise ValueError(f"トピック名の形式が不正: {topic_name!r}")
    if not subscribers:
        raise ValueError("subscribers は 1 件以上必要")
    if message_ttl_days < 1:
        raise ValueError(f"メッセージの寿命は 1 日以上: {message_ttl_days}")
    if max_delivery_count < 1:
        raise ValueError(f"配信回数は 1 以上: {max_delivery_count}")
    if not 0 <= duplicate_detection_days <= MAX_DUPLICATE_DETECTION_DAYS:
        raise ValueError(
            f"重複検出の窓は 0〜{MAX_DUPLICATE_DETECTION_DAYS} 日: {duplicate_detection_days}"
        )
    if duplicate_detection_days >= message_ttl_days:
        raise ValueError(
            "重複検出の窓はメッセージの寿命より短くする: "
            f"{duplicate_detection_days} >= {message_ttl_days}"
        )

    topic: dict = {
        "defaultMessageTimeToLive": _iso_days(message_ttl_days),
        "requiresDuplicateDetection": duplicate_detection_days > 0,
        "enablePartitioning": True,
        "supportOrdering": False,
        "maxSizeInMegabytes": 1024,
    }
    if duplicate_detection_days > 0:
        topic["duplicateDetectionHistoryTimeWindow"] = _iso_days(duplicate_detection_days)

    subscriptions: dict[str, dict] = {}
    for sub_name, filter_expression in sorted(subscribers.items()):
        if not _SUBSCRIPTION_NAME_RE.match(sub_name):
            raise ValueError(
                f"サブスクリプション名は英数字・ピリオド・ハイフン・アンダースコアで"
                f" 1〜50 文字: {sub_name!r}"
            )
        if filter_expression is not None and ";" in filter_expression:
            raise ValueError(f"フィルタ式に ; は使えない: {filter_expression!r}")
        entry: dict = {
            "properties": {
                "defaultMessageTimeToLive": _iso_days(message_ttl_days),
                "maxDeliveryCount": max_delivery_count,
                "deadLetteringOnMessageExpiration": True,
                # フィルタに合わずに捨てられたことを気付けるようにする
                "deadLetteringOnFilterEvaluationExceptions": True,
                "requiresSession": False,
            },
            # 既定では $Default という全通過ルールが 1 本入る。
            # 絞り込むときは消してから自前のルールを足す
            "default_rule_to_delete": None,
            "rule": None,
        }
        if filter_expression is not None:
            entry["default_rule_to_delete"] = DEFAULT_RULE_NAME
            entry["rule"] = {
                "name": f"{sub_name}-filter",
                "properties": {
                    "filterType": "SqlFilter",
                    "sqlFilter": {"sqlExpression": filter_expression},
                },
            }
        subscriptions[sub_name] = entry

    return {"topic": topic, "subscriptions": subscriptions}
