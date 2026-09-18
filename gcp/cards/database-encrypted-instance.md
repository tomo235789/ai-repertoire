---
id: database-encrypted-instance
lang: gcp
title: 保存時暗号化を有効にしたデータベースインスタンスを作る
tags: [CloudSQL, CMEK, 限定公開IP, IAM認証, cloud-sql, cmek, private-ip, iam-auth]
lib: gcp.sql
fn: encrypted_instance_config
since: "2024"
verified: 2026-09-19
status: public
---

「保存データを自分の鍵で暗号化し、限定公開 IP からだけ TLS で繋ぐ」という要求から Cloud SQL のインスタンス定義を組み立てる。API は呼ばない。

## Signature

```python
def encrypted_instance_config(name: str, region: str, *, project_id: str, database_version: str = 'POSTGRES_16', tier: str = 'db-custom-2-7680', disk_size_gb: int = 100, private_network: str | None = None, kms_key_name: str | None = None, availability_type: str = 'REGIONAL', deletion_protection: bool = True, authorized_networks=()) -> dict
```

## Usage

```python
body = encrypted_instance_config(
    "example-db", "asia-northeast1",
    private_network="projects/my-project/global/networks/example-vpc",
)
service.instances().insert(project="my-project", body=body).execute()
```

## Contract

- 限定公開 IP だけのときは `ipv4Enabled` が `False`。`authorized_networks` を渡すと `True` になり、CIDR 順に並ぶ
- `sslMode` は `"ENCRYPTED_ONLY"`。非推奨の `requireSsl` は併用できないので出さない
- IAM 認証のフラグが常に `on`。名前はエンジンで違い、PostgreSQL は `cloudsql.iam_authentication`、MySQL は `cloudsql_iam_authentication`。SQL Server は対応していないので `ValueError`
- `kms_key_name` を渡したときだけ `diskEncryptionConfiguration` が入る。省略すると Google 管理鍵
- `deletionProtectionEnabled` は常に `True`。`deletion_protection=False` は `ValueError`
- 限定公開 IP も許可ネットワークも無いと `ValueError`
- `ValueError`: 名前や版の形式違い、`<プロジェクト>:<インスタンス>` が 98 文字超、IAM 認証に対応しないエンジン、ディスクが 10 GB 未満、可用性が `ZONAL` / `REGIONAL` 以外、許可ネットワークの CIDR が不正かプレフィックス長 0
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/database-encrypted-instance.py` — RDS の保存時暗号化
- `azure/examples/database-encrypted-instance.py` — PostgreSQL フレキシブルサーバー
- 運用を任せたいなら Cloud SQL ではなく AlloyDB や Spanner を検討する
- バックアップの保持は `database-backup-retention` で別に設定する

## Pitfalls

- 顧客管理鍵は Cloud SQL のサービスアカウントに暗号化・復号のロールを先に与える。与えないと作成が失敗する
- 鍵はインスタンスと同じリージョンのキーリングに置く。多リージョンの鍵は使えない
- 限定公開 IP を使うには、VPC にプライベートサービス接続のレンジを先に確保する
- 公開 IP の許可 CIDR にプレフィックス長 0（`0.0.0.0/0` や `::/0`）は渡せない。世界中から接続できてしまうため `ValueError` にしている
- IAM 認証を有効にしても、既存のパスワードユーザーは残る。使わせたくないなら別に削除する

## Test

`examples/database-encrypted-instance_test.py`
