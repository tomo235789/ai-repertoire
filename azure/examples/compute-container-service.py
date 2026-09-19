"""カード compute-container-service: コンテナを常駐サービスとして動かす構成を組み立てる純粋関数。

`azure-mgmt-appcontainers` の `container_apps.begin_create_or_update` に渡す
ContainerApp の body を返す。API は呼ばず、資格情報も環境変数も読まない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
# Container Apps の CPU とメモリは 0.25 コアあたり 0.5 GiB の比で固定されている
_MEMORY_GIB_PER_CPU = 2.0
_ALLOWED_CPU = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)
# [HOST[:PORT]/]PATH[:TAG] と [HOST[:PORT]/]PATH@sha256:<64 桁>
_TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]{0,127}$")
_REPOSITORY_RE = re.compile(r"^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_HOST_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?(:\d{1,5})?$")


def _split_image(image: str) -> tuple[str, str, str]:
    """イメージ参照を (ホスト, リポジトリ, タグかダイジェスト) に分ける。

    ホストは `.` か `:` を含むか `localhost` の先頭要素。無ければ空文字。
    """
    head, _, rest = image.partition("/")
    if rest and ("." in head or ":" in head or head == "localhost"):
        host, remainder = head, rest
    else:
        host, remainder = "", image
    repository, sep, reference = remainder.partition("@")
    if sep:
        return host, repository, reference
    # タグの `:` はパスの最後の要素にしか現れない
    repository, sep, reference = remainder.rpartition(":")
    if not sep:
        return host, remainder, ""
    if "/" in reference:
        return host, remainder, ""
    return host, repository, reference
_UAMI_RE = re.compile(
    r"^/subscriptions/[^/]+/resourceGroups/[^/]+"
    r"/providers/Microsoft\.ManagedIdentity/userAssignedIdentities/[^/]+$"
)


def container_service_config(
    name: str,
    image: str,
    managed_environment_id: str,
    *,
    target_port: int = 8080,
    external_ingress: bool = False,
    cpu: float = 0.5,
    min_replicas: int = 1,
    max_replicas: int = 10,
    env: dict[str, str] | None = None,
    registry_server: str | None = None,
    registry_identity: str = "system",
) -> dict:
    """常駐コンテナサービスの構成を返す。

    Args:
        name: Container App 名。英小文字・数字・ハイフンで 2〜32 文字
        image: コンテナイメージ。タグは省略せず、latest は使わない
        managed_environment_id: 配置先マネージド環境の ARM リソース ID
        target_port: コンテナが待ち受けるポート
        external_ingress: True でインターネットに公開、False で環境内部のみ
        cpu: 割り当てる CPU コア数。0.25 刻みで 2.0 まで
        min_replicas: 最小レプリカ数。0 にするとアイドル時に課金されない
        max_replicas: 最大レプリカ数
        env: コンテナに渡す環境変数。秘密情報は入れない
        registry_server: プライベートレジストリのホスト名
        registry_identity: レジストリ認証に使うマネージド ID。"system" かユーザー割り当て ID の ARM ID

    Returns:
        location 抜きの ContainerApp body（properties を持つ dict）

    Raises:
        ValueError: 名前の形式違い、イメージにタグが無いか latest、ポートが範囲外、
            CPU が許可された値でない、レプリカ数が不正、
            registry_identity が "system" でも ARM リソース ID でもない場合
    """
    if not _NAME_RE.fullmatch(name) or not 2 <= len(name) <= 32:
        raise ValueError(f"Container App 名は英小文字・数字・ハイフンで 2〜32 文字: {name!r}")
    host, repository, reference = _split_image(image)
    if host and not _HOST_RE.fullmatch(host):
        raise ValueError(f"レジストリのホスト名が不正: {image!r}")
    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError(f"イメージのリポジトリ名が不正: {image!r}")
    if "@" in image:
        if not _DIGEST_RE.fullmatch(reference):
            raise ValueError(f"ダイジェストは <repo>@sha256:<64 桁> の形にする: {image!r}")
    elif not reference:
        raise ValueError(f"イメージにタグを付ける（ダイジェスト固定が望ましい）: {image!r}")
    elif not _TAG_RE.fullmatch(reference):
        raise ValueError(f"タグの形式が不正: {image!r}")
    elif reference == "latest":
        raise ValueError("latest タグはリビジョンを再現できないので使わない")
    if not 1 <= target_port <= 65535:
        raise ValueError(f"ポートが範囲外: {target_port}")
    if cpu not in _ALLOWED_CPU:
        raise ValueError(f"CPU は {_ALLOWED_CPU} のいずれか: {cpu}")
    if min_replicas < 0 or max_replicas < 1 or min_replicas > max_replicas:
        raise ValueError(
            f"レプリカ数が不正: min={min_replicas} max={max_replicas}"
        )

    configuration: dict = {
        "activeRevisionsMode": "Single",
        "ingress": {
            "external": external_ingress,
            "targetPort": target_port,
            "transport": "auto",
            # Container Apps 側で HTTP を HTTPS にリダイレクトさせる
            "allowInsecure": False,
            "traffic": [{"latestRevision": True, "weight": 100}],
        },
    }
    if registry_identity != "system" and not _UAMI_RE.fullmatch(registry_identity):
        raise ValueError(
            "registry_identity は \"system\" かユーザー割り当て ID の ARM リソース ID: "
            f"{registry_identity!r}"
        )
    if registry_server is not None:
        # パスワードを持たせず、マネージド ID でレジストリに認証する
        configuration["registries"] = [
            {"server": registry_server, "identity": registry_identity}
        ]

    container: dict = {
        "name": name,
        "image": image,
        "resources": {"cpu": cpu, "memory": f"{cpu * _MEMORY_GIB_PER_CPU:g}Gi"},
    }
    if env:
        container["env"] = [{"name": k, "value": v} for k, v in sorted(env.items())]

    if registry_identity == "system":
        identity: dict = {"type": "SystemAssigned"}
    else:
        # レジストリをユーザー割り当て ID で引くなら、その ID をアプリにも付ける
        identity = {
            "type": "SystemAssigned, UserAssigned",
            "userAssignedIdentities": {registry_identity: {}},
        }

    return {
        "identity": identity,
        "properties": {
            "managedEnvironmentId": managed_environment_id,
            "configuration": configuration,
            "template": {
                "containers": [container],
                "scale": {"minReplicas": min_replicas, "maxReplicas": max_replicas},
            },
        },
    }
