"""カード network-private-endpoint: Private Service Connect のエンドポイントを
組み立てる純粋関数。

Compute Engine の `globalForwardingRules.insert` / `forwardingRules.insert` に渡す
リソースと、名前解決に使う DNS の設定を返す。API は呼ばない。
"""

from __future__ import annotations

import ipaddress
import re

_NAME_RE = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")
# Google API バンドル向けの転送ルール名は英小文字と数字だけで 20 文字まで
_BUNDLE_NAME_RE = re.compile(r"^[a-z][a-z0-9]{0,19}$")

# Google API へ閉域で出るときのバンドルと、対応する DNS 名
API_BUNDLES: dict[str, tuple[str, str]] = {
    # バンドル名 -> (転送先, プライベート DNS ゾーン)
    "all-apis": ("all-apis", "p.googleapis.com"),
    "vpc-sc": ("vpc-sc", "p.googleapis.com"),
}
# 限定公開の Google アクセスで使う VIP レンジ。
# Private Service Connect のエンドポイントには自分で予約した内部 IP を使うので、
# これは「同じバンドルを VIP で使う場合の対応表」であって推奨アドレスではない
PRIVATE_GOOGLE_ACCESS_VIP_RANGES = {
    "all-apis": "199.36.153.8/30",
    "vpc-sc": "199.36.153.4/30",
}


def private_endpoint_config(
    name: str,
    network: str,
    ip_address: str,
    *,
    target_service: str | None = None,
    api_bundle: str | None = None,
    subnetwork: str | None = None,
    allow_psc_global_access: bool = False,
) -> dict:
    """公開 IP を通さずに繋ぐエンドポイントの設定を返す。

    Args:
        name: エンドポイント名
        network: 接続元の VPC
        ip_address: エンドポイントに割り当てる内部 IP
        target_service: 公開されたサービスのアタッチメント。個別サービスへ繋ぐとき
        api_bundle: Google API のバンドル名。API_BUNDLES のキー
        subnetwork: 個別サービスへ繋ぐときのサブネット
        allow_psc_global_access: 他リージョンからの接続を許すか

    Returns:
        forwarding_rule と dns_zone を持つ dict

    Raises:
        ValueError: 名前の形式違い（バンドル向けは英小文字と数字で 20 文字まで）、
            IP アドレスが不正、API バンドル向けに IPv6 を指定、
            target_service と api_bundle をどちらも指定しないか両方指定した場合、
            個別サービスにサブネットを渡さなかった場合
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"エンドポイント名の形式が不正: {name!r}")
    try:
        parsed_ip = ipaddress.ip_address(ip_address)
    except ValueError as exc:
        raise ValueError(f"IP アドレスが不正: {ip_address!r}") from exc
    if (target_service is None) == (api_bundle is None):
        raise ValueError("target_service か api_bundle のどちらか一方を指定する")

    if api_bundle is not None:
        if api_bundle not in API_BUNDLES:
            raise ValueError(f"未知のバンドル: {api_bundle!r}")
        # Google API へのバンドルは IPv4 の仮想 IP でしか作れない
        if parsed_ip.version != 4:
            raise ValueError(f"API バンドルへのエンドポイントは IPv4 のみ: {ip_address!r}")
        if not _BUNDLE_NAME_RE.fullmatch(name):
            raise ValueError(
                f"バンドル向けの転送ルール名は英小文字と数字で 20 文字まで: {name!r}"
            )
        target, dns_suffix = API_BUNDLES[api_bundle]
        rule = {
            "name": name,
            "network": network,
            "IPAddress": ip_address,
            "target": target,
            # Google API へのバンドルはグローバル転送ルールで作る
            "loadBalancingScheme": "",
        }
        dns_zone = {
            "dns_name": f"{dns_suffix}.",
            "visibility": "private",
            "networks": [network],
            "records": [{"name": f"*.{dns_suffix}.", "type": "A", "rrdatas": [ip_address]}],
        }
        return {"forwarding_rule": rule, "dns_zone": dns_zone, "scope": "global"}

    if subnetwork is None:
        raise ValueError("個別サービスへのエンドポイントにはサブネットが要る")
    rule = {
        "name": name,
        "network": network,
        "subnetwork": subnetwork,
        "IPAddress": ip_address,
        "target": target_service,
        "loadBalancingScheme": "",
        "allowPscGlobalAccess": allow_psc_global_access,
    }
    return {"forwarding_rule": rule, "dns_zone": None, "scope": "regional"}
