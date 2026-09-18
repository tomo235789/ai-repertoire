"""カード network-security-group-minimal: 必要なポートだけを開ける NSG 規則を組み立てる純粋関数。

`azure-mgmt-network` の `network_security_groups.begin_create_or_update` に渡す
securityRules を返す。API は呼ばない。
"""

from __future__ import annotations

import ipaddress

# 受信規則の優先度。若いほど先に評価される
_FIRST_PRIORITY = 100
_PRIORITY_STEP = 10
# 明示的な拒否をユーザー規則の最後に置く（既定規則より前で落とす）
_DENY_PRIORITY = 4000

# インターネットに開けると事故になりやすい管理用ポート
MANAGEMENT_PORTS = frozenset({22, 3389, 5985, 5986})
# 送信元に指定すると全世界からの着信を許すサービスタグ。
# CIDR で書いた 0.0.0.0/0 と ::/0 はプレフィックス長 0 として同じ扱いにする
INTERNET_TAGS = frozenset({"*", "Internet"})


def _check_source(source: str, port: int) -> None:
    """送信元が全世界を指していないかを、IPv4 と IPv6 の両方で見る"""
    if source in INTERNET_TAGS:
        unrestricted = True
    elif source[:1].isalpha():
        # VirtualNetwork や AzureLoadBalancer のようなサービスタグは範囲を持たない
        return
    else:
        try:
            network = ipaddress.ip_network(source, strict=True)
        except ValueError as exc:
            raise ValueError(f"送信元は CIDR かサービスタグを指定する: {source!r}") from exc
        unrestricted = network.prefixlen == 0

    if unrestricted and port in MANAGEMENT_PORTS:
        raise ValueError(
            f"管理用ポート {port} をインターネット全体に開けない。"
            "踏み台か Bastion、Just-In-Time アクセスを使う"
        )


def minimal_inbound_rules(
    allowed: tuple[tuple[str, int], ...] | list[tuple[str, int]],
    *,
    protocol: str = "Tcp",
) -> list[dict]:
    """許可する (送信元, ポート) の組だけを開け、残りを明示的に拒否する規則を返す。

    Args:
        allowed: (送信元, ポート) の組。送信元は CIDR かサービスタグ
        protocol: "Tcp" / "Udp" / "*"

    Returns:
        優先度順に並んだ securityRules のリスト。最後は全拒否

    Raises:
        ValueError: allowed が空、ポートが範囲外、送信元の形式違い、
            管理用ポートをインターネットに開こうとした、規則が多すぎる場合
    """
    allowed = tuple(allowed)
    if not allowed:
        raise ValueError("allowed は 1 件以上必要")
    if protocol not in {"Tcp", "Udp", "*"}:
        raise ValueError(f"protocol は Tcp / Udp / * のいずれか: {protocol!r}")

    # 同じ組を 2 度書いても規則は 1 本にする
    unique = sorted(set(allowed))
    if _FIRST_PRIORITY + _PRIORITY_STEP * len(unique) >= _DENY_PRIORITY:
        raise ValueError("規則が多すぎる。送信元をまとめるか NSG を分ける")

    rules: list[dict] = []
    for index, (source, port) in enumerate(unique):
        if not 1 <= port <= 65535:
            raise ValueError(f"ポートが範囲外: {port}")
        _check_source(source, port)
        rules.append(
            {
                # 名前に使えるのは英数字・ハイフン・アンダースコア・ピリオドなので、
                # 送信元そのものではなく並び順から決める
                "name": f"allow-{index:03d}-port-{port}",
                "properties": {
                    "protocol": protocol,
                    "sourceAddressPrefix": source,
                    "sourcePortRange": "*",
                    "destinationAddressPrefix": "*",
                    "destinationPortRange": str(port),
                    "access": "Allow",
                    "direction": "Inbound",
                    "priority": _FIRST_PRIORITY + _PRIORITY_STEP * index,
                },
            }
        )

    rules.append(
        {
            "name": "deny-all-inbound",
            "properties": {
                "protocol": "*",
                "sourceAddressPrefix": "*",
                "sourcePortRange": "*",
                "destinationAddressPrefix": "*",
                "destinationPortRange": "*",
                "access": "Deny",
                "direction": "Inbound",
                "priority": _DENY_PRIORITY,
            },
        }
    )
    return rules
