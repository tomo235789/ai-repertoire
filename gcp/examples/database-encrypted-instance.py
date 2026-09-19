"""カード database-encrypted-instance: 保存時暗号化を有効にした DB を組み立てる純粋関数。

Cloud SQL Admin API の `instances.insert` に渡す DatabaseInstance を返す。
API は呼ばず、パスワードも作らない。
"""

from __future__ import annotations

import ipaddress
import re

_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,96}[a-z0-9]$")
_VERSION_RE = re.compile(r"^(POSTGRES|MYSQL|SQLSERVER)_[0-9_A-Z]+$")

AVAILABILITY_TYPES = ("ZONAL", "REGIONAL")
# Cloud SQL の接続名 <プロジェクト>:<インスタンス> の上限
MAX_CONNECTION_NAME = 98

# IAM 認証を有効にするフラグ名。SQL Server は IAM 認証に対応していない
IAM_AUTH_FLAGS = {
    "POSTGRES": "cloudsql.iam_authentication",
    "MYSQL": "cloudsql_iam_authentication",
}


def encrypted_instance_config(
    name: str,
    region: str,
    *,
    project_id: str,
    database_version: str = "POSTGRES_16",
    tier: str = "db-custom-2-7680",
    disk_size_gb: int = 100,
    private_network: str | None = None,
    kms_key_name: str | None = None,
    availability_type: str = "REGIONAL",
    deletion_protection: bool = True,
    authorized_networks: tuple[str, ...] | list[str] = (),
) -> dict:
    """保存時暗号化と閉域接続を前提にしたインスタンスの構成を返す。

    Args:
        name: インスタンス名
        region: リージョン
        project_id: プロジェクト ID。接続名の長さを検査するために使う
        database_version: データベースの版
        tier: マシンタイプ
        disk_size_gb: ディスク容量。10 GB 以上
        private_network: 限定公開 IP を割り当てる VPC の完全名
        kms_key_name: 顧客管理鍵の完全名。省略すると Google 管理鍵
        availability_type: AVAILABILITY_TYPES のいずれか
        deletion_protection: 削除保護
        authorized_networks: 公開 IP を使うときに許可する CIDR

    Returns:
        instances.insert に渡せる DatabaseInstance dict

    Raises:
        ValueError: 名前や版の形式違い、接続名が 98 文字超、
            IAM 認証に対応しないエンジン、許可ネットワークが IPv4 でない、
            ディスクが 10 GB 未満、未知の可用性、許可ネットワークの CIDR が不正か
            プレフィックス長 0、限定公開 IP も許可ネットワークも無い、
            削除保護を切ろうとした場合
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"インスタンス名の形式が不正: {name!r}")
    connection_name = f"{project_id}:{name}"
    if len(connection_name) > MAX_CONNECTION_NAME:
        raise ValueError(
            f"<プロジェクト>:<インスタンス> は {MAX_CONNECTION_NAME} 文字まで:"
            f" {connection_name!r}"
        )
    if not _VERSION_RE.fullmatch(database_version):
        raise ValueError(f"データベースの版の形式が不正: {database_version!r}")
    if disk_size_gb < 10:
        raise ValueError(f"ディスクは 10 GB 以上: {disk_size_gb}")
    engine = database_version.split("_", 1)[0]
    if engine not in IAM_AUTH_FLAGS:
        raise ValueError(f"IAM 認証に対応していないエンジン: {engine}")
    if availability_type not in AVAILABILITY_TYPES:
        raise ValueError(f"可用性は {AVAILABILITY_TYPES} のいずれか: {availability_type!r}")
    if not deletion_protection:
        raise ValueError("削除保護を切ると誤操作でインスタンスごと失う")
    if private_network is None and not authorized_networks:
        raise ValueError(
            "限定公開 IP か許可ネットワークのどちらかは要る。両方無いと誰も接続できない"
        )

    checked_networks = []
    for cidr in sorted(set(authorized_networks)):
        try:
            network = ipaddress.ip_network(cidr, strict=True)
        except ValueError as exc:
            raise ValueError(f"許可ネットワークの CIDR が不正: {cidr!r}") from exc
        if network.version != 4:
            raise ValueError(f"許可ネットワークは IPv4 で指定する: {cidr!r}")
        if network.prefixlen == 0:
            raise ValueError(
                f"公開 IP を全世界に開けない: {cidr}。接続元の範囲を絞る"
            )
        checked_networks.append(str(network))

    ip_configuration: dict = {
        "ipv4Enabled": bool(checked_networks),
        # 接続は TLS 必須にする。requireSsl は非推奨で sslMode と併用できない
        "sslMode": "ENCRYPTED_ONLY",
        "authorizedNetworks": [
            {"name": f"allow-{index}", "value": cidr}
            for index, cidr in enumerate(checked_networks)
        ],
    }
    if private_network is not None:
        ip_configuration["privateNetwork"] = private_network
        ip_configuration["enablePrivatePathForGoogleCloudServices"] = True

    settings: dict = {
        "tier": tier,
        "availabilityType": availability_type,
        "dataDiskSizeGb": disk_size_gb,
        "dataDiskType": "PD_SSD",
        "storageAutoResize": True,
        "deletionProtectionEnabled": True,
        "ipConfiguration": ip_configuration,
        "databaseFlags": [
            # IAM 認証を使い、パスワードの配布をやめる。フラグ名はエンジンで違う
            {"name": IAM_AUTH_FLAGS[engine], "value": "on"}
        ],
    }

    instance: dict = {
        "name": name,
        "region": region,
        "databaseVersion": database_version,
        "settings": settings,
    }
    if kms_key_name is not None:
        instance["diskEncryptionConfiguration"] = {"kmsKeyName": kms_key_name}
    return instance
