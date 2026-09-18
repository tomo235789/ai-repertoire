---
id: compute-serverless-function
lang: azure
title: イベント駆動のサーバーレス関数を配置する
tags: [関数アプリ, サーバーレス, マネージドID, アプリ設定, functions, serverless, managed-identity, app-settings]
lib: azure.functions
fn: serverless_function_config
since: "2024"
verified: 2026-09-19
status: public
---

「このランタイムでイベントを受けて動く関数を置く。鍵は持たせない」という要求から関数アプリの構成を組み立てる。API は呼ばない。

## Signature

```python
def serverless_function_config(name: str, runtime: str, storage_account_name: str, server_farm_id: str, *, app_insights_connection_string: str | None = None, app_settings: dict[str, str] | None = None, always_on: bool = False) -> dict
```

## Usage

```python
cfg = serverless_function_config(
    "example-fn", "python3.12", "examplestorage", plan_id,
    app_settings={"MY_FLAG": "on"},
)
client.web_apps.begin_create_or_update(
    "example-rg", "example-fn", {"location": "japaneast", **cfg}
).result()
```

## Contract

- ストレージへの接続は `AzureWebJobsStorage__accountName` と `AzureWebJobsStorage__credential: "managedidentity"`。接続文字列の `AzureWebJobsStorage` は作らない
- `identity` は常にシステム割り当て
- `httpsOnly` は `True`、`minTlsVersion` は `"1.2"`、`ftpsState` は `"Disabled"`
- `alwaysOn` は `always_on` をそのまま反映する。従量課金プランでは効かない
- アプリ設定は名前順に並ぶ。予約済みのキーを `app_settings` で上書きすると `ValueError`
- 値に `AccountKey=` や `SharedAccessKey=` が含まれると `ValueError`。秘密は Key Vault 参照で渡す
- `ValueError`: 名前が英小文字・数字・ハイフンの 3〜60 文字でない、`RUNTIMES` に無いランタイム
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/compute-serverless-function.py` — Lambda 関数の設定
- `gcp/examples/compute-serverless-function.py` — Cloud Functions（第 2 世代）
- 常駐させたいなら `compute-container-service` を使う。関数の従量課金より読みやすい構成になる
- 秘密を渡すだけなら `secret-fetch-at-runtime` の Key Vault 参照を組み合わせる

## Pitfalls

- マネージド ID でストレージに繋ぐには、関数アプリの ID に Storage Blob Data Owner と Queue Data Contributor を先に与える。与える前に作るとホストが起動しない
- `WEBSITE_RUN_FROM_PACKAGE=1` の関数アプリはファイルシステムが読み取り専用。実行時に書き込む処理は一時ディレクトリを使う
- 従量課金プランでは `alwaysOn` が効かない。常時起動が要るならプランを変える。Flex Consumption では `functionAppConfig.alwaysReady` で台数を指定する別の仕組みになる
- アプリ設定の変更はアプリの再起動を伴う。デプロイ中の設定変更で処理が落ちることがある
- 関数アプリ名はグローバルに一意。`<name>.azurewebsites.net` として公開される

## Test

`examples/compute-serverless-function_test.py`
