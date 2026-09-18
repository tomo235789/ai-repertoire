"""必要なポートだけを開けるセキュリティグループの設定を組み立てる純粋関数。

出力は boto3 ``ec2`` クライアントの ``create_security_group`` /
``authorize_security_group_ingress`` / ``authorize_security_group_egress`` /
``revoke_security_group_egress`` に渡す kwargs。API は呼ばない。
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

# 管理用ポート。全世界からの開放を禁止する
_ADMIN_PORTS = frozenset({22, 3389})
_ANY_V4 = "0.0.0.0/0"
_ANY_V6 = "::/0"

# create_security_group が自動で付ける既定の egress（全許可）。egress_all=False のとき取り消す
DEFAULT_EGRESS_ALLOW_ALL: dict = {"IpProtocol": "-1", "IpRanges": [{"CidrIp": _ANY_V4}]}


@dataclass(frozen=True)
class Rule:
    """ingress 規則 1 つ。cidr か source_sg のどちらか一方を指定する"""

    port: int
    description: str
    cidr: str | None = None
    source_sg: str | None = None
    protocol: str = "tcp"
    to_port: int | None = None


def _validate_port(port: int) -> None:
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        raise ValueError(f"port は 0〜65535 の整数: {port!r}")


def _permission(rule: Rule) -> dict:
    if not rule.description or not rule.description.strip():
        raise ValueError("description は必須")
    if (rule.cidr is None) == (rule.source_sg is None):
        raise ValueError("cidr と source_sg はどちらか一方だけ指定する")
    if rule.protocol not in ("tcp", "udp"):
        raise ValueError(f"protocol は tcp か udp（全プロトコル許可は不可）: {rule.protocol}")
    _validate_port(rule.port)
    to_port = rule.port if rule.to_port is None else rule.to_port
    _validate_port(to_port)
    if to_port < rule.port:
        raise ValueError(f"to_port は port 以上: {rule.port}-{to_port}")

    perm: dict = {"IpProtocol": rule.protocol, "FromPort": rule.port, "ToPort": to_port}
    if rule.source_sg is not None:
        if not rule.source_sg.startswith("sg-"):
            raise ValueError(f"source_sg は sg-xxxx の形式: {rule.source_sg}")
        perm["UserIdGroupPairs"] = [{"GroupId": rule.source_sg, "Description": rule.description}]
        return perm

    try:
        net = ipaddress.ip_network(rule.cidr, strict=True)
    except ValueError as e:
        raise ValueError(f"cidr が不正: {rule.cidr} ({e})") from e
    if net.prefixlen == 0 and any(rule.port <= p <= to_port for p in _ADMIN_PORTS):
        raise ValueError(f"{rule.cidr} からポート {rule.port}-{to_port}（22 / 3389 を含む）は開放できない")
    if net.version == 4:
        perm["IpRanges"] = [{"CidrIp": str(net), "Description": rule.description}]
    else:
        perm["Ipv6Ranges"] = [{"CidrIpv6": str(net), "Description": rule.description}]
    return perm


def minimal_security_group(
    name: str,
    vpc_id: str,
    ingress: list[Rule],
    egress_all: bool = False,
    description: str | None = None,
) -> dict:
    """最小限のセキュリティグループの boto3 kwargs を返す。

    - ``create_security_group``: グループ本体
    - ``authorize_ingress``: ``IpPermissions`` に渡すリスト（規則ごとに 1 要素）
    - ``authorize_egress``: ``egress_all=True`` のときだけ全許可 1 要素、それ以外は空
    - ``revoke_egress``: ``egress_all=False`` のとき、作成時に自動付与される全許可 egress を取り消す 1 要素
    """
    if not name:
        raise ValueError("name は空にできない")
    if not vpc_id.startswith("vpc-"):
        raise ValueError(f"vpc_id は vpc-xxxx の形式: {vpc_id}")

    permissions = [_permission(rule) for rule in ingress]
    return {
        "create_security_group": {
            "GroupName": name,
            "Description": description or name,
            "VpcId": vpc_id,
        },
        "authorize_ingress": permissions,
        "authorize_egress": [DEFAULT_EGRESS_ALLOW_ALL] if egress_all else [],
        "revoke_egress": [] if egress_all else [DEFAULT_EGRESS_ALLOW_ALL],
    }
