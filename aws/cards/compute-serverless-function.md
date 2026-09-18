---
id: compute-serverless-function
lang: aws
title: イベント駆動のサーバーレス関数を配置する
tags: [サーバーレス, 関数, Lambda, serverless, function, lambda, x-ray, concurrency]
lib: aws.lambda
fn: lambda_function
since: "2024"
verified: 2026-09-18
status: public
---

S3 上の Zip パッケージから Lambda 関数を組み立てる。X-Ray トレース有効、秘密情報を環境変数に置かせない。出力は boto3 `lambda` の `create_function` / `put_function_concurrency` の kwargs。

## Signature

```python
lambda_function(name: str, runtime: str, handler: str, role_arn: str, code: dict, env: dict[str, str] | None = None, reserved_concurrency: int | None = None, timeout: int = 3, memory: int = 128) -> dict
```

## Usage

```python
from importlib import import_module

lambda_function = import_module("compute-serverless-function").lambda_function
cfg = lambda_function("fn", "python3.12", "app.handler", "arn:aws:iam::123456789012:role/fn",
                      {"S3Bucket": "app-artifacts", "S3Key": "fn/1.2.3.zip"},
                      env={"LOG_LEVEL": "info"}, reserved_concurrency=5, timeout=30, memory=512)
# cfg["create_function"]          -> lambda.create_function(**...)  TracingConfig Active、Publish True
# cfg["put_function_concurrency"] -> lambda.put_function_concurrency(**...)（reserved_concurrency 無しなら None）
```

## Contract

- 副作用無し。同じ入力から同じ出力。出力の `Code` / `Variables` は引数と別オブジェクト。出力は `json.dumps` できる
- `create_function` は `PackageType: Zip`、`TracingConfig: {"Mode": "Active"}`、`Publish: True`。既定は `Timeout: 3`、`MemorySize: 128`
- `timeout` は 1〜900、`memory` は 128〜10240、`reserved_concurrency` は 0 以上。範囲外は `ValueError`
- `code` は `S3Bucket` + `S3Key`（+ `S3ObjectVersion`）のみ。`ZipFile`（bytes で JSON 化不可）や `ImageUri` は `ValueError`
- `env` のキーが `SECRET` / `PASSWORD` / `PASSWD` / `TOKEN` / `API_KEY` / `PRIVATE_KEY` を含む（大文字小文字不問）と `ValueError`。`AWS_` 始まりや英数字と `_` 以外の名前、文字列でない値も `ValueError`
- `env` を渡さなければ `Environment` を出さない。`reserved_concurrency` を渡さなければ `put_function_concurrency` は `None`
- `name` / `runtime` / `handler` が空、`role_arn` が `arn:aws:iam::` 始まりでないときは `ValueError`

## Alternatives

- Terraform: `terraform/modules/compute-serverless-function`（同じ ID。`aws_lambda_function`）
- CloudFormation / SAM: `AWS::Lambda::Function` / `AWS::Serverless::Function`
- 秘密情報は secret-fetch-at-runtime（Secrets Manager / Parameter Store から実行時に取得）。常駐で良いなら compute-container-service

## Pitfalls

- `runtime` の廃止スケジュールは検証していない。廃止済みランタイムは `create_function` が `InvalidParameterValueException` で拒否する
- `put_function_concurrency` はアカウントの同時実行上限（既定 1000）から予約分を引く。`ReservedConcurrentExecutions: 0` は関数の実行停止になる
- `Publish: True` で `$LATEST` と同時にバージョン 1 が作られる。エイリアスで参照するなら応答 `Version` を使う
- 環境変数は KMS で暗号化されるが、`get_function_configuration` 権限があれば平文で読める。秘密は置かない
- VPC 内で動かすなら `VpcConfig`（サブネットは network-private-subnet、SG は network-security-group-minimal）と `AWSLambdaVPCAccessExecutionRole` を足す。`FunctionName` はリージョン内で一意で、作成後に変更できない

## Test

`examples/compute-serverless-function_test.py`
