"""イベント駆動のサーバーレス関数（Lambda）の設定を組み立てる純粋関数。

出力は boto3 ``lambda`` クライアントの ``create_function`` / ``put_function_concurrency`` の kwargs。API は呼ばない。
"""

from __future__ import annotations

import re

_TIMEOUT_RANGE = range(1, 900 + 1)
_MEMORY_RANGE = range(128, 10240 + 1)
_ENV_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
# 秘密情報をそのまま環境変数に置かないためのキー名の検査（secret-fetch-at-runtime へ誘導）
_SECRET_LIKE = re.compile(r"(SECRET|PASSWORD|PASSWD|TOKEN|API_KEY|PRIVATE_KEY)", re.IGNORECASE)


def _validate_code(code: dict) -> dict:
    keys = set(code)
    if not keys <= {"S3Bucket", "S3Key", "S3ObjectVersion"}:
        raise ValueError(f"code は S3Bucket / S3Key (/ S3ObjectVersion) のみ（ZipFile / ImageUri は不可）: {sorted(keys)}")
    if not code.get("S3Bucket") or not code.get("S3Key"):
        raise ValueError("code には S3Bucket と S3Key が必要")
    return dict(code)


def _validate_env(env: dict[str, str]) -> dict[str, str]:
    for key, value in env.items():
        if not _ENV_KEY.match(key) or key.startswith("AWS_"):
            raise ValueError(f"環境変数名が不正（英数字と _、AWS_ 始まりは予約）: {key!r}")
        if _SECRET_LIKE.search(key):
            raise ValueError(f"秘密情報は環境変数に置かず Secrets Manager から実行時に取得する: {key!r}")
        if not isinstance(value, str):
            raise ValueError(f"環境変数の値は文字列: {key}={value!r}")
    return dict(env)


def lambda_function(
    name: str,
    runtime: str,
    handler: str,
    role_arn: str,
    code: dict,
    env: dict[str, str] | None = None,
    reserved_concurrency: int | None = None,
    timeout: int = 3,
    memory: int = 128,
) -> dict:
    """Lambda 関数 1 つ分の boto3 kwargs を返す。

    - ``create_function``: S3 上の Zip パッケージ、X-Ray トレース有効
    - ``put_function_concurrency``: ``reserved_concurrency`` を渡したときだけ。無ければ None
    """
    if not name or not runtime or not handler:
        raise ValueError("name / runtime / handler は空にできない")
    if not role_arn.startswith("arn:aws:iam::"):
        raise ValueError(f"role_arn は IAM ロールの ARN: {role_arn}")
    if timeout not in _TIMEOUT_RANGE:
        raise ValueError(f"timeout は 1〜900 秒: {timeout}")
    if memory not in _MEMORY_RANGE:
        raise ValueError(f"memory は 128〜10240 MB: {memory}")
    if reserved_concurrency is not None and reserved_concurrency < 0:
        raise ValueError(f"reserved_concurrency は 0 以上: {reserved_concurrency}")

    create: dict = {
        "FunctionName": name,
        "Runtime": runtime,
        "Handler": handler,
        "Role": role_arn,
        "Code": _validate_code(code),
        "PackageType": "Zip",
        "Timeout": timeout,
        "MemorySize": memory,
        "TracingConfig": {"Mode": "Active"},
        "Publish": True,
    }
    if env:
        create["Environment"] = {"Variables": _validate_env(env)}

    concurrency = None
    if reserved_concurrency is not None:
        concurrency = {"FunctionName": name, "ReservedConcurrentExecutions": reserved_concurrency}
    return {"create_function": create, "put_function_concurrency": concurrency}
