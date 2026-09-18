---
id: compute-serverless-function
lang: terraform
title: イベント駆動のサーバーレス関数を配置する
tags: [サーバーレス, 関数, Lambda, lambda-function, serverless, x-ray, log-retention]
lib: hashicorp/aws
fn: aws_lambda_function
since: "5.0"
verified: 2026-09-18
status: public
---

Zip かコンテナイメージの Lambda 関数を、X-Ray トレースと保持期間付きロググループとともに配置する。パッケージは `filename` と `image_uri` のどちらか一方。

## Signature

```hcl
variables: function_name, role_arn, filename | image_uri, source_code_hash = null, runtime, handler, environment = {}, timeout = 30, memory_size = 256, reserved_concurrent_executions = -1, tracing_mode = "Active", log_retention_days = 30, tags = {}
outputs:   function_arn, function_name, invoke_arn, log_group_name
```

## Usage

```hcl
module "order_events" {
  source           = "./modules/compute-serverless-function"
  function_name    = "order-events"
  role_arn         = "arn:aws:iam::123456789012:role/order-events"
  filename         = "build/order-events.zip"
  source_code_hash = filebase64sha256("build/order-events.zip")
  runtime          = "python3.12"
  handler          = "app.handler"
}
```

## Contract

- `filename` を渡すと `package_type = "Zip"`、`image_uri` を渡すと `"Image"`。両方・どちらも無しは validation で拒否
- Zip では `runtime` と `handler` が必須、Image では指定不可。validation で拒否
- `tracing_config.mode` は既定で `Active`（全呼び出しを X-Ray でトレース）。`PassThrough` に変えられる
- ロググループ `/aws/lambda/<function_name>` を `log_retention_days`（既定 30 日）付きで関数より先に作る。Lambda の自動作成（無期限保持）に任せない
- `reserved_concurrent_executions` は既定 `-1`（予約なし）。`-2` 以下は拒否
- `environment` が空ならブロックを作らない。空でなければ `variables` にそのまま入る
- `timeout` は 1〜900、`memory_size` は 128〜10240 のみ。それ以外は validation で拒否
- `tags` を関数とロググループに付ける

## Alternatives

- 常時稼働やリクエストごとに 15 分を超える処理は compute-container-service
- パッケージが 50 MB を超える、あるいはネイティブ依存が多いなら `image_uri`（コンテナイメージ、最大 10 GB）
- 秘密情報は `environment` に入れず、secret-fetch-at-runtime で実行時に取得する
- VPC 内リソースに接続するなら `vpc_config` を足す（この module は VPC 外で動かす）

## Pitfalls

- `function_name` の変更は再作成になる。`package_type` の変更（Zip ↔ Image）も再作成
- `filename` だけではコードの変更を検知しない。`source_code_hash = filebase64sha256(filename)` を渡す
- `reserved_concurrent_executions = 0` は呼び出しの停止、`-1` は予約なし。誤って `0` にすると全呼び出しがスロットルされる
- 関数の実行ロールにはログ出力（`logs:CreateLogStream`、`logs:PutLogEvents`）と、`Active` なら X-Ray（`xray:PutTraceSegments`）の許可が要る。ロググループは module が作るので `logs:CreateLogGroup` は不要

## Test

`modules/compute-serverless-function/tests/compute-serverless-function.tftest.hcl`
