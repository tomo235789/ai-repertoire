"""カード network-security-group-minimal: 必要なポートだけを開ける VPC ファイアウォール規則を
組み立てる純粋関数。

Compute Engine の `firewalls.insert` に渡すリソースの列を返す。API は呼ばない。
"""

from __future__ import annotations

import ipaddress
import re

_NAME_RE = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")

# 番号が小さいほど先に評価される
_ALLOW_PRIORITY = 1000
_DENY_PRIORITY = 65000

# インターネットに開けると事故になりやすい管理用ポート
MANAGEMENT_PORTS = frozenset({22, 3389, 5985, 5986})
# Identity-Aware Proxy の TCP 転送が使う送信元レンジ
IAP_SOURCE_RANGE = "35.235.240.0/20"
# ファイアウォール名は 1〜63 文字。接尾辞を足しても収まる長さにタグを制限する
MAX_FIREWALL_NAME = 63
_LONGEST_SUFFIX = "-deny-all"


def minimal_firewall_rules(
    network: str,
    target_tag: str,
    allowed: tuple[tuple[str, int], ...] | list[tuple[str, int]],
    *,
    protocol: str = "tcp",
) -> list[dict]:
    """許可する (送信元 CIDR, ポート) の組だけを開け、残りを落とす規則を返す。

    Args:
        network: VPC の名前かセルフリンク
        target_tag: 規則を適用するネットワークタグ
        allowed: (送信元 CIDR, ポート) の組
        protocol: "tcp" / "udp"

    Returns:
        許可規則（優先度 1000）と全拒否規則（優先度 65000）のリスト

    Raises:
        ValueError: タグの形式違い、タグが長すぎて規則名が 63 文字を超える、
            allowed が空、ポートが範囲外、CIDR の形式違い、
            管理用ポートを 0.0.0.0/0 に開こうとした場合
    """
    if not _NAME_RE.match(target_tag):
        raise ValueError(f"ネットワークタグの形式が不正: {target_tag!r}")

    if protocol not in {"tcp", "udp"}:
        raise ValueError(f"protocol は tcp か udp: {protocol!r}")
    allowed = tuple(allowed)
    if not allowed:
        raise ValueError("allowed は 1 件以上必要")

    # 送信元ごとにポートをまとめる（規則の数を増やさない）
    by_source: dict[str, list[int]] = {}
    for source, port in allowed:
        if not 1 <= port <= 65535:
            raise ValueError(f"ポートが範囲外: {port}")
        try:
            network_obj = ipaddress.ip_network(source, strict=True)
        except ValueError as exc:
            raise ValueError(f"送信元は CIDR を指定する: {source!r}") from exc
        if port in MANAGEMENT_PORTS and network_obj.prefixlen == 0:
            raise ValueError(
                f"管理用ポート {port} を 0.0.0.0/0 に開けない。"
                f"Identity-Aware Proxy の {IAP_SOURCE_RANGE} か踏み台を使う"
            )
        by_source.setdefault(str(network_obj), []).append(port)

    # 許可規則の連番の桁数と "-deny-all" のうち、長い方が名前の上限を決める
    longest_suffix = max(len(_LONGEST_SUFFIX), len(f"-allow-{len(by_source) - 1}"))
    if len(target_tag) + longest_suffix > MAX_FIREWALL_NAME:
        raise ValueError(
            f"規則名が {MAX_FIREWALL_NAME} 文字を超える。ネットワークタグは"
            f" {MAX_FIREWALL_NAME - longest_suffix} 文字までにする: {target_tag!r}"
        )

    rules: list[dict] = []
    for index, (source, ports) in enumerate(sorted(by_source.items())):
        rules.append(
            {
                "name": f"{target_tag}-allow-{index}",
                "network": network,
                "direction": "INGRESS",
                "priority": _ALLOW_PRIORITY,
                "sourceRanges": [source],
                "targetTags": [target_tag],
                "allowed": [
                    {"IPProtocol": protocol, "ports": [str(p) for p in sorted(set(ports))]}
                ],
                "logConfig": {"enable": True},
            }
        )

    rules.append(
        {
            "name": f"{target_tag}-deny-all",
            "network": network,
            "direction": "INGRESS",
            "priority": _DENY_PRIORITY,
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": [target_tag],
            "denied": [{"IPProtocol": "all"}],
            "logConfig": {"enable": True},
        }
    )
    return rules
