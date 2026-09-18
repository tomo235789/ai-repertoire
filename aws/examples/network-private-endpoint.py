"""インターネットを経由せずにマネージドサービスへ接続する VPC エンドポイントの設定を組み立てる純粋関数。

出力は boto3 ``ec2.create_vpc_endpoint`` の kwargs。API は呼ばない。
"""

from __future__ import annotations

# Gateway 型が使えるサービス（S3 / DynamoDB のみ）
_GATEWAY_SERVICES = ("s3", "dynamodb")


def _check_ids(label: str, ids: list[str] | None, prefix: str) -> list[str]:
    if not ids:
        raise ValueError(f"{label} は 1 つ以上必要")
    bad = [i for i in ids if not i.startswith(prefix)]
    if bad:
        raise ValueError(f"{label} は {prefix}xxxx の形式: {bad}")
    return list(ids)


def private_endpoint(
    vpc_id: str,
    service_name: str,
    endpoint_type: str,
    subnet_ids: list[str] | None = None,
    security_group_ids: list[str] | None = None,
    route_table_ids: list[str] | None = None,
) -> dict:
    """VPC エンドポイント 1 つ分の ``create_vpc_endpoint`` kwargs を返す。

    - ``Interface``: ``subnet_ids`` と ``security_group_ids`` が必須。``PrivateDnsEnabled`` を True にする
    - ``Gateway``: ``route_table_ids`` が必須。S3 / DynamoDB のみ。``PrivateDnsEnabled`` は付けない
    - 型に合わない引数を渡すと ValueError（黙って捨てない）
    """
    if not vpc_id.startswith("vpc-"):
        raise ValueError(f"vpc_id は vpc-xxxx の形式: {vpc_id}")
    if not service_name or "." not in service_name:
        raise ValueError(f"service_name は com.amazonaws.<region>.<service> の形式: {service_name!r}")
    if endpoint_type not in ("Interface", "Gateway"):
        raise ValueError(f"endpoint_type は Interface か Gateway: {endpoint_type!r}")

    out: dict = {
        "VpcId": vpc_id,
        "ServiceName": service_name,
        "VpcEndpointType": endpoint_type,
    }
    if endpoint_type == "Interface":
        if route_table_ids:
            raise ValueError("Interface 型に route_table_ids は指定できない")
        out["SubnetIds"] = _check_ids("subnet_ids", subnet_ids, "subnet-")
        out["SecurityGroupIds"] = _check_ids("security_group_ids", security_group_ids, "sg-")
        out["PrivateDnsEnabled"] = True
        return out

    if subnet_ids or security_group_ids:
        raise ValueError("Gateway 型に subnet_ids / security_group_ids は指定できない")
    if service_name.rsplit(".", 1)[-1] not in _GATEWAY_SERVICES:
        raise ValueError(f"Gateway 型は S3 / DynamoDB のみ: {service_name}")
    out["RouteTableIds"] = _check_ids("route_table_ids", route_table_ids, "rtb-")
    return out
