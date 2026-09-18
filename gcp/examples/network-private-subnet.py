"""カード network-private-subnet: 外から直接届かないサブネットを組み立てる純粋関数。

Compute Engine の `subnetworks.insert` に渡すリソースを返す。API は呼ばない。
"""

from __future__ import annotations

import ipaddress
import re

_NAME_RE = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")

# フローログのサンプリング率。1.0 は全件
_MAX_SAMPLE_RATE = 1.0
# GCP が各サブネットで予約するアドレス数（ネットワーク、ゲートウェイ、予備、ブロードキャスト）
RESERVED_ADDRESSES = 4
# 主レンジも副レンジも /4 から /29 まで
MIN_PREFIX_LENGTH = 4
MAX_PREFIX_LENGTH = 29


def private_subnet_config(
    name: str,
    network: str,
    ip_cidr_range: str,
    region: str,
    *,
    secondary_ranges: dict[str, str] | None = None,
    flow_log_sampling: float = 0.5,
    purpose: str = "PRIVATE",
) -> dict:
    """外部 IP を持たないワークロード向けのサブネットを返す。

    Args:
        name: サブネット名
        network: 所属する VPC の名前かセルフリンク
        ip_cidr_range: 主レンジの CIDR。/29 まで
        region: リージョン
        secondary_ranges: 副レンジ名 -> CIDR。GKE の Pod / Service 用
        flow_log_sampling: フローログのサンプリング率。0 より大きく 1.0 以下
        purpose: サブネットの用途

    Returns:
        subnetworks.insert に渡せるリソースと、参考情報の usable_addresses

    Raises:
        ValueError: 名前や CIDR の形式違い、ホスト部が残っている、
            プレフィックス長が /4〜/29 の外、purpose が PRIVATE 以外、
            副レンジが主レンジや他の副レンジと重なる、サンプリング率が範囲外の場合
    """
    if not _NAME_RE.match(name):
        raise ValueError(f"サブネット名の形式が不正: {name!r}")
    if not 0 < flow_log_sampling <= _MAX_SAMPLE_RATE:
        raise ValueError(f"サンプリング率は 0 より大きく 1.0 以下: {flow_log_sampling}")

    try:
        primary = ipaddress.ip_network(ip_cidr_range, strict=True)
    except ValueError as exc:
        raise ValueError(f"CIDR が不正: {ip_cidr_range!r}") from exc
    if primary.version != 4:
        raise ValueError("IPv4 の CIDR を指定する")
    if not MIN_PREFIX_LENGTH <= primary.prefixlen <= MAX_PREFIX_LENGTH:
        raise ValueError(
            f"サブネットは /{MIN_PREFIX_LENGTH}〜/{MAX_PREFIX_LENGTH}: {ip_cidr_range}"
        )
    if purpose != "PRIVATE":
        raise ValueError(
            f"この関数はワークロード用のサブネットだけを作る（purpose=PRIVATE）: {purpose!r}"
        )

    secondary_list: list[dict] = []
    accepted_secondaries: list[tuple[str, ipaddress.IPv4Network]] = []
    for range_name, cidr in sorted((secondary_ranges or {}).items()):
        if not _NAME_RE.match(range_name):
            raise ValueError(f"副レンジ名の形式が不正: {range_name!r}")
        try:
            secondary = ipaddress.ip_network(cidr, strict=True)
        except ValueError as exc:
            raise ValueError(f"副レンジの CIDR が不正: {cidr!r}") from exc
        if secondary.version != 4:
            raise ValueError(f"副レンジは IPv4 で指定する: {cidr!r}")
        if not MIN_PREFIX_LENGTH <= secondary.prefixlen <= MAX_PREFIX_LENGTH:
            raise ValueError(
                f"副レンジは /{MIN_PREFIX_LENGTH}〜/{MAX_PREFIX_LENGTH}: {cidr}"
            )
        if secondary.overlaps(primary):
            raise ValueError(f"副レンジが主レンジと重なる: {cidr} と {ip_cidr_range}")
        for accepted_name, accepted in accepted_secondaries:
            if secondary.overlaps(accepted):
                raise ValueError(
                    f"副レンジ同士が重なる: {range_name}={cidr} と {accepted_name}={accepted}"
                )
        accepted_secondaries.append((range_name, secondary))
        secondary_list.append({"rangeName": range_name, "ipCidrRange": str(secondary)})

    resource: dict = {
        "name": name,
        "network": network,
        "ipCidrRange": str(primary),
        "region": region,
        "purpose": purpose,
        # 外部 IP を持たない VM から Google API へ内部経路で出す
        "privateIpGoogleAccess": True,
        "logConfig": {
            "enable": True,
            "aggregationInterval": "INTERVAL_5_SEC",
            "flowSampling": flow_log_sampling,
            "metadata": "INCLUDE_ALL_METADATA",
        },
    }
    if secondary_list:
        resource["secondaryIpRanges"] = secondary_list

    return {
        "subnetwork": resource,
        "usable_addresses": primary.num_addresses - RESERVED_ADDRESSES,
    }
