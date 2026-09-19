---
id: database-encrypted-instance
lang: azure
title: 保存時暗号化を有効にしたデータベースインスタンスを作る
tags: [PostgreSQL, 保存時暗号化, 顧客管理鍵, 閉域, postgresql, encryption-at-rest, cmk, private-access]
lib: azure.sql
fn: encrypted_server_config
since: "2024"
verified: 2026-09-19
status: public
---

「保存データを暗号化し、公衆ネットワークからは繋がせず、パスワード認証も使わない」という要求から PostgreSQL フレキシブルサーバーの構成を組み立てる。API は呼ばない。

## Signature

```python
def encrypted_server_config(name: str, location: str, admin_login: str, *, version: str = '16', sku_name: str = 'Standard_D2ds_v5', storage_gb: int = 128, delegated_subnet_id: str | None = None, private_dns_zone_id: str | None = None, key_vault_key_uri: str | None = None, user_assigned_identity_id: str | None = None, high_availability: str = 'ZoneRedundant') -> dict
```

## Usage

```python
cfg = encrypted_server_config(
    "example-db", "japaneast", "appadmin",
    delegated_subnet_id=subnet_id, private_dns_zone_id=zone_id,
)
client.servers.begin_create("example-rg", "example-db", cfg).result()
```

## Contract

- `authConfig` は Entra ID 認証だけ有効で、パスワード認証は無効
- `publicNetworkAccess` は常に `"Disabled"`
- 鍵を渡さなければ `dataEncryption` は `{"type": "SystemManaged"}` で `identity` は `{"type": "None"}`
- `key_vault_key_uri` と `user_assigned_identity_id` は両方揃えて渡す。片方だけだと `ValueError`
- `delegated_subnet_id` と `private_dns_zone_id` も両方揃えて渡す。片方だけだと `ValueError`
- 高可用性の既定はゾーン冗長。`HA_MODES` に無い値は `ValueError`
- `ValueError`: サーバー名が英小文字・数字・ハイフンの 3〜63 文字でない、ログイン名の形式違い、`postgres` などの予約済みログイン名、ストレージが 32 GB 未満
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/database-encrypted-instance.py` — RDS の保存時暗号化と KMS キー
- `gcp/examples/database-encrypted-instance.py` — Cloud SQL の CMEK と限定公開 IP
- 単一データベースで足りるなら Azure SQL Database の Transparent Data Encryption を使う
- バックアップの保持や地理冗長は `database-backup-retention` で別に設定する

## Pitfalls

- 顧客管理鍵はユーザー割り当て ID でしか読めない。システム割り当て ID では設定できない
- 閉域構成（委任サブネット）と公開アクセスは後から切り替えられない。作り直しになる
- 委任サブネットは `Microsoft.DBforPostgreSQL/flexibleServers` に委任済みで、他のリソースが入っていない必要がある
- パスワード認証を無効にすると、Entra ID の管理者を別に設定するまで誰も接続できない
- ゾーン冗長の高可用性はリージョンによって使えない。使えないリージョンでは作成が失敗する

## Test

`examples/database-encrypted-instance_test.py`
