"""カード compute-serverless-function の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("compute-serverless-function")
lambda_function = mod.lambda_function

CODE = {"S3Bucket": "app-artifacts", "S3Key": "fn/1.2.3.zip"}
ROLE = "arn:aws:iam::123456789012:role/fn"


def test_snapshot():
    """出力の形（boto3 kwargs）"""
    out = lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, env={"LOG_LEVEL": "info"}, reserved_concurrency=5)
    assert out == {
        "create_function": {
            "FunctionName": "fn",
            "Runtime": "python3.12",
            "Handler": "app.handler",
            "Role": ROLE,
            "Code": {"S3Bucket": "app-artifacts", "S3Key": "fn/1.2.3.zip"},
            "PackageType": "Zip",
            "Timeout": 3,
            "MemorySize": 128,
            "TracingConfig": {"Mode": "Active"},
            "Publish": True,
            "Environment": {"Variables": {"LOG_LEVEL": "info"}},
        },
        "put_function_concurrency": {"FunctionName": "fn", "ReservedConcurrentExecutions": 5},
    }
    json.dumps(out)


def test_defaults_and_optional_keys_omitted():
    """timeout 3 / memory 128 が既定。env 無しなら Environment を出さず、concurrency は None"""
    out = lambda_function("fn", "python3.12", "app.handler", ROLE, CODE)
    assert out["create_function"]["Timeout"] == 3
    assert out["create_function"]["MemorySize"] == 128
    assert "Environment" not in out["create_function"]
    assert out["put_function_concurrency"] is None
    assert out["create_function"]["TracingConfig"] == {"Mode": "Active"}
    json.dumps(out)


@pytest.mark.parametrize("timeout", [0, 901, -1])
def test_timeout_out_of_range_rejected(timeout):
    """timeout は 1〜900"""
    with pytest.raises(ValueError):
        lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, timeout=timeout)
    assert lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, timeout=900)["create_function"]["Timeout"] == 900


@pytest.mark.parametrize("memory", [127, 10241, 0])
def test_memory_out_of_range_rejected(memory):
    """memory は 128〜10240"""
    with pytest.raises(ValueError):
        lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, memory=memory)
    assert lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, memory=10240)["create_function"]["MemorySize"] == 10240


def test_reserved_concurrency_zero_allowed_negative_rejected():
    """0（実行停止）は許可、負数は ValueError"""
    out = lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, reserved_concurrency=0)
    assert out["put_function_concurrency"] == {"FunctionName": "fn", "ReservedConcurrentExecutions": 0}
    with pytest.raises(ValueError):
        lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, reserved_concurrency=-1)


@pytest.mark.parametrize(
    "code",
    [{}, {"S3Bucket": "b"}, {"S3Key": "k"}, {"ZipFile": b"PK"}, {"ImageUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/fn:1"}],
)
def test_code_must_be_s3_zip(code):
    """code は S3Bucket + S3Key のみ。ZipFile / ImageUri は ValueError"""
    with pytest.raises(ValueError):
        lambda_function("fn", "python3.12", "app.handler", ROLE, code)


@pytest.mark.parametrize(
    "env",
    [
        {"DB_PASSWORD": "x"},
        {"api_key": "x"},
        {"GITHUB_TOKEN": "x"},
        {"DB_PASSWD": "x"},
        {"SSH_PRIVATE_KEY": "x"},
        {"AWS_REGION": "us-east-1"},
        {"1BAD": "x"},
        {"BAD-NAME": "x"},
        {"PORT": 8080},
    ],
)
def test_secret_like_or_invalid_env_rejected(env):
    """秘密情報らしいキー・予約名・不正な名前・非文字列の値は ValueError"""
    with pytest.raises(ValueError):
        lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, env=env)


def test_s3_object_version_allowed():
    """S3ObjectVersion は Code にそのまま入る"""
    code = {**CODE, "S3ObjectVersion": "v1"}
    assert lambda_function("fn", "python3.12", "app.handler", ROLE, code)["create_function"]["Code"] == code


def test_invalid_required_args_rejected():
    """空の name / runtime / handler、IAM 以外の ARN は ValueError"""
    for kwargs in ({"name": ""}, {"runtime": ""}, {"handler": ""}, {"role_arn": "arn:aws:s3:::b"}):
        base = {"name": "fn", "runtime": "python3.12", "handler": "app.handler", "role_arn": ROLE, "code": CODE}
        with pytest.raises(ValueError):
            lambda_function(**{**base, **kwargs})


def test_is_deterministic_and_copies_input():
    """同じ入力から同じ出力。出力の Code / Variables は引数と別オブジェクト"""
    env = {"LOG_LEVEL": "info"}
    a = lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, env=env)
    b = lambda_function("fn", "python3.12", "app.handler", ROLE, CODE, env=env)
    assert a == b
    assert a["create_function"]["Code"] is not CODE
    assert a["create_function"]["Environment"]["Variables"] is not env
