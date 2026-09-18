"""カード compute-serverless-function: イベント駆動の関数を組み立てる純粋関数。

Cloud Functions（第 2 世代）の `functions.create` に渡す Function を返す。
API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")
_MEMORY_RE = re.compile(r"^\d+(Mi|Gi)$")

RUNTIMES = ("python312", "python311", "nodejs20", "go122", "java21")
# 受け付ける到達範囲
INGRESS_SETTINGS = ("ALLOW_ALL", "ALLOW_INTERNAL_ONLY", "ALLOW_INTERNAL_AND_GCLB")
# 実行時間の上限はトリガー種別で違う
MAX_HTTP_TIMEOUT_SECONDS = 3600
MAX_EVENT_TIMEOUT_SECONDS = 540


def serverless_function_config(
    name: str,
    runtime: str,
    entry_point: str,
    source_bucket: str,
    source_object: str,
    service_account: str,
    *,
    memory: str = "256Mi",
    timeout_seconds: int = 60,
    max_instances: int = 100,
    event_trigger_topic: str | None = None,
    retry_on_failure: bool | None = None,
    ingress: str = "ALLOW_INTERNAL_ONLY",
    env: dict[str, str] | None = None,
) -> dict:
    """イベントで起動する関数の構成を返す。

    Args:
        name: 関数名
        runtime: RUNTIMES のいずれか
        entry_point: 呼び出す関数の名前
        source_bucket: ソースを置いたバケット
        source_object: ソースのオブジェクト名
        service_account: 実行に使うサービスアカウントのメールアドレス
        memory: メモリ量
        timeout_seconds: 1 回の実行の上限。1〜3600
        max_instances: 最大インスタンス数
        event_trigger_topic: 起動元の Pub/Sub トピック。None なら HTTP 関数
        retry_on_failure: 失敗時にイベントを再試行するか。省略するとイベント関数だけ True
        ingress: HTTP 関数の到達範囲
        env: 環境変数。秘密は入れない

    Returns:
        functions.create に渡せる Function dict

    Raises:
        ValueError: 名前やメモリの形式違い、未知のランタイムや ingress、
            インスタンス数が範囲外、タイムアウトが上限超（HTTP 関数は 3600 秒、
            イベント関数は 540 秒）、HTTP 関数に再試行を指定した場合
    """
    if not _NAME_RE.match(name):
        raise ValueError(f"関数名の形式が不正: {name!r}")
    if runtime not in RUNTIMES:
        raise ValueError(f"ランタイムは {RUNTIMES} のいずれか: {runtime!r}")
    if not entry_point:
        raise ValueError("entry_point は空にできない")
    if "@" not in service_account:
        raise ValueError(f"サービスアカウントはメールアドレスで指定する: {service_account!r}")
    if not _MEMORY_RE.match(memory):
        raise ValueError(f"メモリの形式が不正: {memory!r}")
    max_timeout = (
        MAX_HTTP_TIMEOUT_SECONDS if event_trigger_topic is None else MAX_EVENT_TIMEOUT_SECONDS
    )
    if not 1 <= timeout_seconds <= max_timeout:
        raise ValueError(f"タイムアウトは 1〜{max_timeout} 秒: {timeout_seconds}")
    if max_instances < 1:
        raise ValueError(f"最大インスタンス数は 1 以上: {max_instances}")
    if ingress not in INGRESS_SETTINGS:
        raise ValueError(f"ingress は {INGRESS_SETTINGS} のいずれか: {ingress!r}")
    if retry_on_failure is None:
        # イベント関数は再試行あり、HTTP 関数は再試行という概念が無い
        retry_on_failure = event_trigger_topic is not None
    if event_trigger_topic is None and retry_on_failure:
        raise ValueError("HTTP 関数には再試行の設定が無い。retry_on_failure は指定しない")

    environment_variables: dict[str, str] = {}
    for key, value in sorted((env or {}).items()):
        if key.lower().endswith(("password", "secret", "token", "key")):
            raise ValueError(
                f"秘密は環境変数に直接入れない（{key}）。Secret Manager の参照を使う"
            )
        environment_variables[key] = value

    function: dict = {
        "build_config": {
            "runtime": runtime,
            "entry_point": entry_point,
            "source": {
                "storage_source": {"bucket": source_bucket, "object": source_object}
            },
        },
        "service_config": {
            "available_memory": memory,
            "timeout_seconds": timeout_seconds,
            "max_instance_count": max_instances,
            "service_account_email": service_account,
            "ingress_settings": ingress,
            "environment_variables": environment_variables,
            # 送信も既定では内部レンジだけに絞る
            "vpc_connector_egress_settings": "PRIVATE_RANGES_ONLY",
        },
    }
    if event_trigger_topic is not None:
        function["event_trigger"] = {
            "event_type": "google.cloud.pubsub.topic.v1.messagePublished",
            "pubsub_topic": event_trigger_topic,
            "service_account_email": service_account,
            "retry_policy": "RETRY_POLICY_RETRY" if retry_on_failure else "RETRY_POLICY_DO_NOT_RETRY",
        }
    return function
