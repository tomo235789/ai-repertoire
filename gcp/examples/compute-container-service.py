"""カード compute-container-service: コンテナを常駐サービスとして動かす構成を組み立てる純粋関数。

Cloud Run Admin API の `services.create` に渡す Service を返す。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-z]([-a-z0-9]{0,47}[a-z0-9])?$")
_CPU_RE = re.compile(r"^(\d+(\.\d+)?|\d+m)$")
_MEMORY_RE = re.compile(r"^\d+(Mi|Gi)$")

# 外部からの到達範囲。既定は内部とロードバランサ経由だけ
INGRESS_MODES = ("INGRESS_TRAFFIC_ALL", "INGRESS_TRAFFIC_INTERNAL_ONLY",
                 "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER")


def container_service_config(
    name: str,
    image: str,
    service_account: str,
    *,
    cpu: str = "1",
    memory: str = "512Mi",
    min_instances: int = 0,
    max_instances: int = 100,
    concurrency: int = 80,
    ingress: str = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER",
    allow_unauthenticated: bool = False,
    env: dict[str, str] | None = None,
    vpc_connector: str | None = None,
) -> dict:
    """常駐コンテナサービスの構成を返す。

    Args:
        name: サービス名。英小文字・数字・ハイフンで 1〜49 文字
        image: コンテナイメージ。タグは省略せず、latest は使わない
        service_account: 実行に使うサービスアカウントのメールアドレス
        cpu: CPU 量。"1" や "500m"
        memory: メモリ量。"512Mi" や "1Gi"
        min_instances: 最小インスタンス数。0 でアイドル時に課金されない
        max_instances: 最大インスタンス数
        concurrency: 1 インスタンスが同時に受ける要求数
        ingress: INGRESS_MODES のいずれか
        allow_unauthenticated: 認証なしの呼び出しを許すか
        env: 環境変数。秘密は入れない
        vpc_connector: VPC コネクタの名前。VPC 内のリソースへ出るとき

    Returns:
        service と iam_policy を持つ dict

    Raises:
        ValueError: 名前やイメージの形式違い、latest タグ、CPU やメモリの形式違い、
            インスタンス数や同時実行数が不正、未知の ingress、
            環境変数に秘密らしい値を入れた場合
    """
    if not _NAME_RE.match(name):
        raise ValueError(f"サービス名は英小文字・数字・ハイフンで 1〜49 文字: {name!r}")
    if ":" not in image.rsplit("/", 1)[-1] and "@sha256:" not in image:
        raise ValueError(f"イメージにタグかダイジェストを付ける: {image!r}")
    if image.rsplit(":", 1)[-1] == "latest":
        raise ValueError("latest タグはリビジョンを再現できないので使わない")
    if "@" not in service_account:
        raise ValueError(f"サービスアカウントはメールアドレスで指定する: {service_account!r}")
    if not _CPU_RE.match(cpu):
        raise ValueError(f"CPU の形式が不正: {cpu!r}")
    if not _MEMORY_RE.match(memory):
        raise ValueError(f"メモリの形式が不正: {memory!r}")
    if min_instances < 0 or max_instances < 1 or min_instances > max_instances:
        raise ValueError(f"インスタンス数が不正: min={min_instances} max={max_instances}")
    if not 1 <= concurrency <= 1000:
        raise ValueError(f"同時実行数は 1〜1000: {concurrency}")
    if ingress not in INGRESS_MODES:
        raise ValueError(f"ingress は {INGRESS_MODES} のいずれか: {ingress!r}")

    container: dict = {
        "image": image,
        "resources": {"limits": {"cpu": cpu, "memory": memory}},
    }
    for key, value in sorted((env or {}).items()):
        if key.lower().endswith(("password", "secret", "token", "key")):
            raise ValueError(
                f"秘密は環境変数に直接入れない（{key}）。Secret Manager の参照を使う"
            )
        container.setdefault("env", []).append({"name": key, "value": value})

    template: dict = {
        "containers": [container],
        "service_account": service_account,
        "scaling": {"min_instance_count": min_instances, "max_instance_count": max_instances},
        "max_instance_request_concurrency": concurrency,
        # 起動中だけでなく要求の処理中もリクエストに紐づく課金にする
        "execution_environment": "EXECUTION_ENVIRONMENT_GEN2",
    }
    if vpc_connector is not None:
        template["vpc_access"] = {"connector": vpc_connector, "egress": "PRIVATE_RANGES_ONLY"}

    iam_policy = (
        {"bindings": [{"role": "roles/run.invoker", "members": ["allUsers"]}]}
        if allow_unauthenticated
        else {"bindings": []}
    )

    return {
        "service": {"template": template, "ingress": ingress},
        "iam_policy": iam_policy,
    }
