"""カード queue-fanout-topic: 1 つのイベントを複数の購読者へ配る構成を組み立てる純粋関数。

Pub/Sub のトピックと購読の設定を返す。API は呼ばない。
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9._~+%-]{2,254}$")
_PATH_RE = {
    "topic": re.compile(r"^projects/[^/]+/topics/(.+)$"),
    "subscription": re.compile(r"^projects/[^/]+/subscriptions/(.+)$"),
}


def _check_resource(label: str, kind: str, value: str) -> None:
    """projects/<project>/<種別>/<id> の形と、末尾の ID の形式を見る"""
    match = _PATH_RE[kind].fullmatch(value)
    if match is None:
        raise ValueError(
            f"{label} は projects/<project>/{kind}s/<id> の完全名で指定する: {value!r}"
        )
    resource_id = match.group(1)
    if not _NAME_RE.fullmatch(resource_id):
        raise ValueError(f"{label} の名前の形式が不正: {value!r}")
    if resource_id.lower().startswith("goog"):
        raise ValueError(f"{label} の ID は goog で始められない: {value!r}")



_SERVICE_ACCOUNT_RE = re.compile(
    r"^(?:[a-z][a-z0-9-]{4,28}[a-z0-9]@([a-z][a-z0-9-]{4,28}[a-z0-9])\.iam"
    r"|\d+-compute@(developer))\.gserviceaccount\.com$"
)


def fanout_topic(
    topic: str,
    subscribers: dict[str, dict],
    *,
    subscription_project_number: str | None = None,
    message_retention_days: int = 1,
    schema: str | None = None,
    kms_key_name: str | None = None,
) -> dict:
    """1 つのトピックと、購読者ごとの購読設定を返す。

    Args:
        topic: トピックの完全名
        subscription_project_number: 購読を持つプロジェクトの番号。
            プッシュ配信を使うときは必須。サービスエージェントの IAM を組み立てる
        subscribers: 購読の完全名 -> 設定。設定のキーは
            filter（絞り込み式）、push_endpoint（プッシュ配信先の HTTPS URL）、
            push_service_account（プッシュ時に署名するサービスアカウント）
        message_retention_days: トピック側でメッセージを保持する日数。1〜31
        schema: メッセージスキーマの完全名
        kms_key_name: メッセージを暗号化する鍵の完全名

    Returns:
        topic_config と subscription_configs（購読名順のリスト）を持つ dict

    Raises:
        ValueError: 名前の形式違い、ID が goog で始まる、購読者が空、
            保持日数が範囲外、未知の設定キー、プッシュ配信先が HTTPS でない、
            プッシュの配信先とサービスアカウントが対になっていない、
            プッシュ配信なのにプロジェクト番号が無い場合
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
    token_creator_bindings: list[dict] = []
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
        if ("push_endpoint" in options) != ("push_service_account" in options):
            raise ValueError(
                f"プッシュ配信は配信先と署名するサービスアカウントを対で指定する: {name!r}"
            )
        if "push_endpoint" in options:
            endpoint = options["push_endpoint"]
            parts = urlsplit(endpoint)
            if parts.scheme != "https" or not parts.hostname:
                raise ValueError(
                    f"プッシュ配信先はホスト名を持つ HTTPS の URL にする: {endpoint!r}"
                )
            service_account = options.get("push_service_account")
            if not service_account:
                raise ValueError(
                    f"プッシュ配信には署名するサービスアカウントが要る: {name!r}"
                )
            if not subscription_project_number or not re.fullmatch(
                r"[0-9]+", subscription_project_number
            ):
                raise ValueError(
                    "プッシュ配信には ASCII 数字の subscription_project_number が要る。"
                    "Pub/Sub のサービスエージェントが署名するため: "
                    f"{subscription_project_number!r}"
                )
            config["push_config"] = {
                "push_endpoint": endpoint,
                "oidc_token": {"service_account_email": service_account},
            }
            match = _SERVICE_ACCOUNT_RE.fullmatch(service_account)
            if match is None:
                raise ValueError(
                    "プッシュの署名に使うサービスアカウントは "
                    f"<name>@<project>.iam.gserviceaccount.com の形にする: {service_account!r}"
                )
            sa_project = match.group(1) or match.group(2)
            topic_project = name.split("/")[1]
            if sa_project != topic_project:
                raise ValueError(
                    "プッシュの署名に使うサービスアカウントは購読と同じプロジェクトに置く: "
                    f"{sa_project!r} != {topic_project!r}"
                )
            # サービスエージェントが署名できないとプッシュの JWT を作れない
            token_creator_bindings.append(
                {
                    "resource": f"projects/{sa_project}/serviceAccounts/{service_account}",
                    "role": "roles/iam.serviceAccountTokenCreator",
                    "members": [
                        "serviceAccount:service-"
                        f"{subscription_project_number}@gcp-sa-pubsub.iam.gserviceaccount.com"
                    ],
                }
            )
        subscription_configs.append(config)

    return {
        "topic_config": topic_config,
        "subscription_configs": subscription_configs,
        # プッシュ配信を使う購読ごとに 1 件。購読を作る前に与える
        "token_creator_bindings": token_creator_bindings,
    }
