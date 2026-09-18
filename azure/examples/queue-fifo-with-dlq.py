"""カード queue-fifo-with-dlq: 順序保証と配信不能キュー付きのキューを組み立てる純粋関数。

`azure-mgmt-servicebus` の `queues.create_or_update` に渡す SBQueue の
プロパティを返す。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]{0,258}[A-Za-z0-9]$")

# 期間は ISO 8601 の duration で渡す。ロックは 5 分が上限
MAX_LOCK_SECONDS = 300
# 重複検出の窓は 20 秒から 7 日まで
MIN_DUPLICATE_DETECTION_SECONDS = 20
MAX_DUPLICATE_DETECTION_SECONDS = 7 * 86400
# パーティション分割しないキューで選べる容量（MB）
ALLOWED_SIZES_MEGABYTES = (1024, 2048, 3072, 4096, 5120)


def _iso_duration(seconds: int) -> str:
    """秒数を ISO 8601 の duration に変換する（例: 90 -> "PT1M30S"）"""
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    date_part = f"{days}D" if days else ""
    time_part = "".join(
        f"{value}{unit}"
        for value, unit in ((hours, "H"), (minutes, "M"), (secs, "S"))
        if value
    )
    if not date_part and not time_part:
        return "PT0S"
    return f"P{date_part}" + (f"T{time_part}" if time_part else "")


def fifo_queue_with_dlq(
    name: str,
    *,
    lock_seconds: int = 60,
    max_delivery_count: int = 5,
    message_ttl_seconds: int = 14 * 86400,
    duplicate_detection_seconds: int = 600,
    max_size_megabytes: int = 1024,
) -> dict:
    """セッションで順序を保ち、失敗したメッセージを退避するキューの設定を返す。

    Args:
        name: キュー名
        lock_seconds: 受信したメッセージのロック時間。1〜300 秒
        max_delivery_count: この回数まで配信して駄目なら配信不能キューへ送る
        message_ttl_seconds: メッセージの寿命
        duplicate_detection_seconds: 重複検出の窓。0 で無効
        max_size_megabytes: キューの最大サイズ。ALLOWED_SIZES_MEGABYTES のいずれか

    Returns:
        SBQueue のプロパティにそのまま渡せる dict

    Raises:
        ValueError: 名前の形式違い、ロック時間が 1〜300 の外、配信回数が 1 未満、
            寿命が重複検出の窓以下、サイズが対応値以外の場合
    """
    if not _NAME_RE.match(name):
        raise ValueError(f"キュー名の形式が不正: {name!r}")
    if not 1 <= lock_seconds <= MAX_LOCK_SECONDS:
        raise ValueError(f"ロック時間は 1〜{MAX_LOCK_SECONDS} 秒: {lock_seconds}")
    if max_delivery_count < 1:
        raise ValueError(f"配信回数は 1 以上: {max_delivery_count}")
    if max_size_megabytes not in ALLOWED_SIZES_MEGABYTES:
        raise ValueError(
            f"最大サイズは {ALLOWED_SIZES_MEGABYTES} のいずれか: {max_size_megabytes}"
        )
    if duplicate_detection_seconds != 0 and not (
        MIN_DUPLICATE_DETECTION_SECONDS
        <= duplicate_detection_seconds
        <= MAX_DUPLICATE_DETECTION_SECONDS
    ):
        raise ValueError(
            "重複検出の窓は 0（無効）か"
            f" {MIN_DUPLICATE_DETECTION_SECONDS}〜{MAX_DUPLICATE_DETECTION_SECONDS} 秒:"
            f" {duplicate_detection_seconds}"
        )
    if message_ttl_seconds <= duplicate_detection_seconds:
        raise ValueError(
            "メッセージの寿命は重複検出の窓より長くする: "
            f"{message_ttl_seconds} <= {duplicate_detection_seconds}"
        )

    properties: dict = {
        # セッションを必須にして、同じセッション ID のメッセージの順序を保つ
        "requiresSession": True,
        "lockDuration": _iso_duration(lock_seconds),
        "maxDeliveryCount": max_delivery_count,
        "defaultMessageTimeToLive": _iso_duration(message_ttl_seconds),
        # 期限切れも配信不能キューへ送り、黙って消えないようにする
        "deadLetteringOnMessageExpiration": True,
        "maxSizeInMegabytes": max_size_megabytes,
        "enablePartitioning": False,
        "requiresDuplicateDetection": duplicate_detection_seconds > 0,
    }
    if duplicate_detection_seconds > 0:
        properties["duplicateDetectionHistoryTimeWindow"] = _iso_duration(
            duplicate_detection_seconds
        )
    return properties
