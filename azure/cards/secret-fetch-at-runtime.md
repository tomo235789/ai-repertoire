---
id: secret-fetch-at-runtime
lang: azure
title: 秘密情報を実行時にシークレット管理サービスから取得する
tags: [KeyVault, 参照, アプリ設定, ロール割り当て, key-vault, reference, app-settings, secrets-user]
lib: azure.keyvault
fn: runtime_secret_config
since: "2024"
verified: 2026-09-19
status: public
---

「パスワードをコードにも設定にも置かず、起動時に Key Vault から解決させる」という要求から、アプリ設定に書く参照と必要なロール割り当てを組み立てる。秘密の値そのものは扱わない。

## Signature

```python
def key_vault_reference(vault_name: str, secret_name: str, version: str | None = None) -> str
def runtime_secret_config(vault_name: str, secrets: dict[str, str], principal_id: str, *, subscription_id: str, resource_group: str, pin_versions: dict[str, str] | None = None) -> dict
```

## Usage

```python
cfg = runtime_secret_config(
    "example-kv", {"DB_PASSWORD": "db-password"}, principal_id,
    subscription_id="<sub>", resource_group="example-rg",
)
a = cfg["role_assignment"]
auth.role_assignments.create(a["scope"], a["role_assignment_name"], a["parameters"])
web.web_apps.update_application_settings(
    "example-rg", "example-fn",
    {"properties": {s["name"]: s["value"] for s in cfg["app_settings"]}},
)
```

## Contract

- アプリ設定の値は `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>)` の形。秘密の値は返り値に一切入らない
- `pin_versions` を渡すとその環境変数だけ URI にバージョンが付く。省略すると最新を追従する
- アプリ設定は環境変数名順に並ぶ
- 割り当てるロールは Key Vault Secrets User。読み取りだけで、値の書き換えはできない
- 割り当て名はスコープとプリンシパルから `uuid5` で決まる。作り直しても重複しない
- `ValueError`: Key Vault 名やシークレット名の形式違い、バージョンが 32 桁の 16 進でない、`secrets` が空、principal_id が GUID でない、`pin_versions` に `secrets` に無いキーがある
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/secret-fetch-at-runtime.py` — Secrets Manager からの取得と IAM ポリシー
- `gcp/examples/secret-fetch-at-runtime.py` — Secret Manager のバージョン参照
- 証明書なら `secrets` ではなく `certificates` のエンドポイントを使う
- SDK で直接読むなら参照を使わず `SecretClient` と `DefaultAzureCredential` を組む

## Pitfalls

- Key Vault 参照はアプリの起動時に解決される。起動後に秘密を変えても、アプリを再起動するまで古い値のまま
- バージョンを省略すると最新を追うが、更新の反映には最大 24 時間かかる。即時に切り替えたいならバージョンを固定して設定ごと入れ替える
- 参照の解決にはマネージド ID とロール割り当ての両方が要る。割り当て前に起動すると設定値が参照文字列のままアプリへ渡る
- Key Vault が RBAC ではなくアクセスポリシーで動いている場合、このロール割り当ては効かない
- ネットワークを閉じた Key Vault では、アプリ側から到達できる経路（プライベートエンドポイントか信頼されたサービス）が要る

## Test

`examples/secret-fetch-at-runtime_test.py`
