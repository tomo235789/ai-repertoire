"""カード network-private-endpoint の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("network-private-endpoint")
private_endpoint = mod.private_endpoint


def test_snapshot_interface():
    """Interface 型: サブネット + SG、PrivateDnsEnabled=True"""
    out = private_endpoint(
        "vpc-0abc",
        "com.amazonaws.us-east-1.secretsmanager",
        "Interface",
        subnet_ids=["subnet-0a", "subnet-0b"],
        security_group_ids=["sg-0abc"],
    )
    assert out == {
        "VpcId": "vpc-0abc",
        "ServiceName": "com.amazonaws.us-east-1.secretsmanager",
        "VpcEndpointType": "Interface",
        "SubnetIds": ["subnet-0a", "subnet-0b"],
        "SecurityGroupIds": ["sg-0abc"],
        "PrivateDnsEnabled": True,
    }
    json.dumps(out)


def test_snapshot_gateway():
    """Gateway 型: ルートテーブルのみ、PrivateDnsEnabled は付けない"""
    out = private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.s3", "Gateway", route_table_ids=["rtb-0abc"])
    assert out == {
        "VpcId": "vpc-0abc",
        "ServiceName": "com.amazonaws.us-east-1.s3",
        "VpcEndpointType": "Gateway",
        "RouteTableIds": ["rtb-0abc"],
    }
    assert "PrivateDnsEnabled" not in out
    json.dumps(out)


def test_interface_requires_subnets_and_security_groups():
    """Interface 型でサブネットか SG が無いと ValueError"""
    with pytest.raises(ValueError):
        private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.ecr.api", "Interface", subnet_ids=["subnet-0a"])
    with pytest.raises(ValueError):
        private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.ecr.api", "Interface", security_group_ids=["sg-0abc"])
    with pytest.raises(ValueError):
        private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.ecr.api", "Interface", subnet_ids=[], security_group_ids=[])


def test_gateway_requires_route_tables_and_only_s3_dynamodb():
    """Gateway 型でルートテーブルが無い、または S3 / DynamoDB 以外は ValueError"""
    with pytest.raises(ValueError):
        private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.s3", "Gateway")
    with pytest.raises(ValueError):
        private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.sqs", "Gateway", route_table_ids=["rtb-0abc"])
    out = private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.dynamodb", "Gateway", route_table_ids=["rtb-0abc"])
    assert out["RouteTableIds"] == ["rtb-0abc"]


def test_mismatched_args_rejected():
    """型に合わない引数は黙って捨てず ValueError"""
    with pytest.raises(ValueError):
        private_endpoint(
            "vpc-0abc",
            "com.amazonaws.us-east-1.s3",
            "Interface",
            subnet_ids=["subnet-0a"],
            security_group_ids=["sg-0abc"],
            route_table_ids=["rtb-0abc"],
        )
    with pytest.raises(ValueError):
        private_endpoint(
            "vpc-0abc", "com.amazonaws.us-east-1.s3", "Gateway", route_table_ids=["rtb-0abc"], subnet_ids=["subnet-0a"]
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vpc_id": "subnet-0abc"},
        {"service_name": ""},
        {"service_name": "s3"},
        {"endpoint_type": "GatewayLoadBalancer"},
        {"subnet_ids": ["sg-0abc"]},
        {"security_group_ids": ["subnet-0abc"]},
    ],
)
def test_invalid_identifiers_rejected(kwargs):
    """ID の形式違い・空のサービス名・未対応の endpoint_type は ValueError"""
    base = {
        "vpc_id": "vpc-0abc",
        "service_name": "com.amazonaws.us-east-1.ecr.api",
        "endpoint_type": "Interface",
        "subnet_ids": ["subnet-0a"],
        "security_group_ids": ["sg-0abc"],
    }
    with pytest.raises(ValueError):
        private_endpoint(**{**base, **kwargs})


def test_is_deterministic_and_copies_lists():
    """同じ入力から同じ出力。出力のリストは引数と別オブジェクト"""
    subnets = ["subnet-0a"]
    a = private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.logs", "Interface", subnets, ["sg-0abc"])
    b = private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.logs", "Interface", subnets, ["sg-0abc"])
    assert a == b
    assert a["SubnetIds"] is not subnets
