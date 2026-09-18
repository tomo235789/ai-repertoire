"""インターネットから直接到達できないプライベートサブネットの設定を組み立てる純粋関数。

出力は boto3 ``ec2`` クライアントの ``create_subnet`` / ``modify_subnet_attribute`` /
``create_route_table`` にそのまま渡せる kwargs。API は呼ばない。
"""

from __future__ import annotations

import ipaddress

# AWS のサブネットは IPv4 で /16〜/28 のみ
_MIN_PREFIX = 16
_MAX_PREFIX = 28


def _tag_spec(resource_type: str, tags: dict[str, str]) -> list[dict]:
    return [
        {
            "ResourceType": resource_type,
            "Tags": [{"Key": k, "Value": v} for k, v in tags.items()],
        }
    ]


def _validate_cidr(cidr: str, vpc_cidr: str | None) -> ipaddress.IPv4Network:
    try:
        net = ipaddress.ip_network(cidr, strict=True)
    except ValueError as e:
        raise ValueError(f"cidr が不正: {cidr} ({e})") from e
    if not isinstance(net, ipaddress.IPv4Network):
        raise ValueError(f"cidr は IPv4 のみ: {cidr}")
    if not _MIN_PREFIX <= net.prefixlen <= _MAX_PREFIX:
        raise ValueError(f"cidr のプレフィックス長は /{_MIN_PREFIX}〜/{_MAX_PREFIX}: {cidr}")
    if vpc_cidr is not None:
        try:
            vpc = ipaddress.ip_network(vpc_cidr, strict=True)
        except ValueError as e:
            raise ValueError(f"vpc_cidr が不正: {vpc_cidr} ({e})") from e
        if not isinstance(vpc, ipaddress.IPv4Network) or not net.subnet_of(vpc):
            raise ValueError(f"cidr {cidr} は vpc_cidr {vpc_cidr} に含まれない")
    return net


def private_subnet(
    vpc_id: str,
    cidr: str,
    az: str,
    tags: dict[str, str],
    vpc_cidr: str | None = None,
) -> dict:
    """プライベートサブネット 1 つ分の boto3 kwargs を返す。

    - ``create_subnet``: サブネット本体
    - ``modify_subnet_attribute``: パブリック IP の自動付与を無効化（``SubnetId`` は呼び出し側が足す）
    - ``route_table``: ``create_route_table`` の kwargs。IGW への経路は持たない（VPC ローカルのみ）
    """
    if not vpc_id.startswith("vpc-"):
        raise ValueError(f"vpc_id は vpc-xxxx の形式: {vpc_id}")
    if not az:
        raise ValueError("az は空にできない")
    _validate_cidr(cidr, vpc_cidr)
    if not tags:
        raise ValueError("tags は 1 つ以上必要（少なくとも Name）")

    return {
        "create_subnet": {
            "VpcId": vpc_id,
            "CidrBlock": cidr,
            "AvailabilityZone": az,
            "TagSpecifications": _tag_spec("subnet", tags),
        },
        "modify_subnet_attribute": {
            "MapPublicIpOnLaunch": {"Value": False},
        },
        "route_table": {
            "VpcId": vpc_id,
            "TagSpecifications": _tag_spec("route-table", tags),
        },
    }
