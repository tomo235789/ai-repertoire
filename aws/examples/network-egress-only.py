"""外向き通信だけを許可する既定経路を組み立てる純粋関数。

出力は boto3 ``ec2.create_route`` の kwargs のリスト（IPv4 / IPv6 で 1 つずつ）。API は呼ばない。
"""

from __future__ import annotations


def egress_only_route(
    route_table_id: str,
    nat_gateway_id: str | None = None,
    egress_only_igw_id: str | None = None,
) -> list[dict]:
    """外向き専用の既定経路を返す。

    - IPv4 (``0.0.0.0/0``) は NAT Gateway 経由、IPv6 (``::/0``) は Egress-only Internet Gateway 経由
    - 渡された ID の分だけ経路を作る。両方 None なら ValueError
    - Internet Gateway (``igw-``) は入向きも通すので受け付けない
    """
    if not route_table_id.startswith("rtb-"):
        raise ValueError(f"route_table_id は rtb-xxxx の形式: {route_table_id}")
    if nat_gateway_id is None and egress_only_igw_id is None:
        raise ValueError("nat_gateway_id か egress_only_igw_id の少なくとも一方が必要")

    routes: list[dict] = []
    if nat_gateway_id is not None:
        if not nat_gateway_id.startswith("nat-"):
            raise ValueError(f"nat_gateway_id は nat-xxxx の形式（igw- は不可）: {nat_gateway_id}")
        routes.append(
            {
                "RouteTableId": route_table_id,
                "DestinationCidrBlock": "0.0.0.0/0",
                "NatGatewayId": nat_gateway_id,
            }
        )
    if egress_only_igw_id is not None:
        if not egress_only_igw_id.startswith("eigw-"):
            raise ValueError(f"egress_only_igw_id は eigw-xxxx の形式（igw- は不可）: {egress_only_igw_id}")
        routes.append(
            {
                "RouteTableId": route_table_id,
                "DestinationIpv6CidrBlock": "::/0",
                "EgressOnlyInternetGatewayId": egress_only_igw_id,
            }
        )
    return routes
