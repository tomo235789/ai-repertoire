"""カード network-private-endpoint: マネージドサービスへ閉域で繋ぐ構成を組み立てる純粋関数。

`azure-mgmt-network` の `private_endpoints.begin_create_or_update` と
`private_dns_zone_groups.begin_create_or_update` に渡す引数を返す。API は呼ばない。
"""

from __future__ import annotations

import re

# サブリソース（groupId）ごとに使うプライベート DNS ゾーン
PRIVATE_DNS_ZONES: dict[str, str] = {
    "blob": "privatelink.blob.core.windows.net",
    "file": "privatelink.file.core.windows.net",
    "queue": "privatelink.queue.core.windows.net",
    "table": "privatelink.table.core.windows.net",
    "sqlServer": "privatelink.database.windows.net",
    "vault": "privatelink.vaultcore.azure.net",
    "namespace": "privatelink.servicebus.windows.net",
    "registry": "privatelink.azurecr.io",
    "sites": "privatelink.azurewebsites.net",
}

_RESOURCE_ID_RE = re.compile(r"^/subscriptions/[^/]+/resourceGroups/[^/]+/providers/.+$")


def private_endpoint_config(
    name: str,
    subnet_id: str,
    target_resource_id: str,
    group_id: str,
    *,
    manual_approval: bool = False,
    request_message: str = "",
    private_dns_zone_id: str | None = None,
) -> dict:
    """プライベートエンドポイントと、名前解決を差し替える DNS ゾーングループを返す。

    Args:
        name: エンドポイント名
        subnet_id: 配置するサブネットの ARM ID
        target_resource_id: 接続先リソースの ARM ID
        group_id: 接続するサブリソース。PRIVATE_DNS_ZONES のキー
        manual_approval: 接続先の所有者による手動承認を求めるか
        request_message: 手動承認のときに送る依頼文
        private_dns_zone_id: 使うプライベート DNS ゾーンの ARM ID。省略するとゾーングループを作らない

    Returns:
        endpoint と dns_zone_group（省略時は None）、必要なゾーン名 private_dns_zone を持つ dict

    Raises:
        ValueError: 名前が空、サブネット・接続先・DNS ゾーンの ARM ID の形式違い、
            未知の group_id、自動承認なのに依頼文を指定した場合
    """
    if not name:
        raise ValueError("name は空にできない")
    for label, value in (("subnet_id", subnet_id), ("target_resource_id", target_resource_id)):
        if not _RESOURCE_ID_RE.match(value):
            raise ValueError(f"{label} は ARM リソース ID を指定する: {value!r}")
    if group_id not in PRIVATE_DNS_ZONES:
        raise ValueError(f"未知のサブリソース: {group_id!r}")
    if request_message and not manual_approval:
        raise ValueError("request_message は manual_approval=True のときだけ指定する")

    connection = {
        "name": f"{name}-connection",
        "properties": {
            "privateLinkServiceId": target_resource_id,
            "groupIds": [group_id],
        },
    }
    if manual_approval:
        connection["properties"]["requestMessage"] = request_message
        connections_key = "manualPrivateLinkServiceConnections"
    else:
        connections_key = "privateLinkServiceConnections"

    zone = PRIVATE_DNS_ZONES[group_id]
    dns_zone_group = None
    if private_dns_zone_id is not None:
        if not _RESOURCE_ID_RE.match(private_dns_zone_id):
            raise ValueError(
                f"private_dns_zone_id は ARM リソース ID を指定する: {private_dns_zone_id!r}"
            )
        dns_zone_group = {
            "properties": {
                "privateDnsZoneConfigs": [
                    {
                        "name": zone.replace(".", "-"),
                        "properties": {"privateDnsZoneId": private_dns_zone_id},
                    }
                ]
            }
        }

    return {
        "endpoint": {
            "properties": {
                "subnet": {"id": subnet_id},
                "customNetworkInterfaceName": f"{name}-nic",
                connections_key: [connection],
            }
        },
        "dns_zone_group": dns_zone_group,
        "private_dns_zone": zone,
    }
