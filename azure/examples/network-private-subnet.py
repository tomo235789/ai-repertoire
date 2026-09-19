"""カード network-private-subnet: 外から直接届かないサブネットの構成を組み立てる純粋関数。

`azure-mgmt-network` の `subnets.begin_create_or_update` に渡す Subnet を返す。
API は呼ばず、アドレス計算も標準ライブラリだけで行う。
"""

from __future__ import annotations

import ipaddress
import re

_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]{0,78}[A-Za-z0-9_])?$")

# Azure が各サブネットの先頭で予約するアドレス数（ネットワーク、ゲートウェイ 2、ブロードキャスト）
RESERVED_ADDRESSES = 5


def private_subnet_config(
    name: str,
    address_prefix: str,
    *,
    route_table_id: str | None = None,
    nat_gateway_id: str | None = None,
    network_security_group_id: str | None = None,
    service_endpoints: tuple[str, ...] | list[str] = (),
    delegation_service: str | None = None,
) -> dict:
    """インターネットから着信できないサブネットの構成を返す。

    Args:
        name: サブネット名
        address_prefix: CIDR。プレフィックス長は /29 まで
        route_table_id: 既定経路を差し替えるルートテーブルの ARM ID
        nat_gateway_id: 送信のみを許す NAT ゲートウェイの ARM ID
        network_security_group_id: 適用するネットワークセキュリティグループの ARM ID
        service_endpoints: 有効にするサービスエンドポイント。例 ("Microsoft.Storage",)
        delegation_service: サブネットを委任するサービス。例 "Microsoft.App/environments"

    Returns:
        name と properties、参考情報の usable_addresses を持つ dict

    Raises:
        ValueError: 名前の形式違い、CIDR が不正、ホスト部が残っている、
            プレフィックスが /29 より小さい、公開 IP を前提とする設定を混ぜた場合
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"サブネット名の形式が不正: {name!r}")

    try:
        network = ipaddress.ip_network(address_prefix, strict=True)
    except ValueError as exc:
        raise ValueError(f"CIDR が不正: {address_prefix!r}") from exc
    if network.version != 4:
        raise ValueError("IPv4 の CIDR を指定する")
    if network.prefixlen > 29:
        raise ValueError(f"サブネットは /29 まで: {address_prefix}")

    properties: dict = {
        "addressPrefix": str(network),
        # プライベートエンドポイントに NSG を効かせるため、ポリシーは無効にしない
        "privateEndpointNetworkPolicies": "Enabled",
        "privateLinkServiceNetworkPolicies": "Enabled",
        # 既定の送信インターネットアクセスに頼らない（明示した NAT だけを使う）
        "defaultOutboundAccess": False,
        "serviceEndpoints": [{"service": s} for s in sorted(service_endpoints)],
    }
    if route_table_id is not None:
        properties["routeTable"] = {"id": route_table_id}
    if nat_gateway_id is not None:
        properties["natGateway"] = {"id": nat_gateway_id}
    if network_security_group_id is not None:
        properties["networkSecurityGroup"] = {"id": network_security_group_id}
    if delegation_service is not None:
        properties["delegations"] = [
            {
                "name": delegation_service.replace("/", "-").lower(),
                "properties": {"serviceName": delegation_service},
            }
        ]

    return {
        "name": name,
        "properties": properties,
        "usable_addresses": network.num_addresses - RESERVED_ADDRESSES,
    }
