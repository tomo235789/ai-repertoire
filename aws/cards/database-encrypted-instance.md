---
id: database-encrypted-instance
lang: aws
title: 保存時暗号化を有効にしたデータベースインスタンスを作る
tags: [暗号化, PostgreSQL, RDS, 非公開, IAM 認証, secrets-manager, storage-encryption, postgres]
lib: aws.rds
fn: encrypted_postgres
since: "2024"
verified: 2026-09-18
status: public
---

「保存時暗号化・非公開・マスターパスワードを Secrets Manager 管理」の PostgreSQL インスタンスを、rds.create_db_instance の kwargs として組み立てる。

## Signature

```python
def encrypted_postgres(identifier: str, instance_class: str, allocated_storage: int, subnet_group: str, security_group_ids: Sequence[str], kms_key_id: str | None = None, deletion_protection: bool = True, *, engine_version: str | None = None, master_username: str = "app_admin", multi_az: bool = False, tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from database_encrypted_instance import encrypted_postgres  # examples/database-encrypted-instance.py をコピー

kw = encrypted_postgres(
    "app-db", "db.t4g.micro", 20, "app-private-subnet",
    ["sg-0123456789abcdef0"], kms_key_id=KEY, engine_version="16"
)
client.create_db_instance(**kw)  # StorageEncrypted=True / PubliclyAccessible=False
# MasterUserPassword は出力にも含まれない。パスワードは Secrets Manager が管理
```

## Contract

- `StorageEncrypted` は常に `True`。`kms_key_id` 無しなら AWS 管理キー `aws/rds`、有りで `KmsKeyId` + `MasterUserSecretKmsKeyId` に同じ CMK を設定
- `PubliclyAccessible` は `False`（外部公開しない）。`DeletionProtection` は既定 `True`
- `ManageMasterUserPassword` は `True`。出力に `MasterUserPassword` キーを含まない
- `EnableIAMDatabaseAuthentication` は `True`。パスワード認証ではなく IAM 認証を有効にする
- ストレージは固定で `gp3`。`AutoMinorVersionUpgrade` / `CopyTagsToSnapshot` はともに `True`
- `identifier` は小文字英字始まり・英数字と `-`・63 文字以内。`--` や末尾 `-` を許さない
- `allocated_storage` は 20 以上（gp3 の PostgreSQL 最小値）。bool は拒否
- `master_username` は予約語（rdsadmin, admin, rds_superuser）と `1abc` / `app-admin` を拒否
- 同じ入力に同じ出力を返し、入力の `tags` を変更しない。全体を `json.dumps` できる
- `ValueError`: 識別子・インスタンスクラス・ストレージ・サブネットグループ・セキュリティグループの形式チェック失敗

## Alternatives

- Terraform module `terraform/modules/database-encrypted-instance`（同じ id。`aws_db_instance` の `storage_encrypted` / `publicly_accessible` / `manage_master_user_password` を同じ既定値で）
- CloudFormation `AWS::RDS::DBInstance` の `StorageEncrypted` / `PubliclyAccessible` / `ManageMasterUserPassword` プロパティ

## Pitfalls

- 識別子の命名規則は RDS 固有。大文字・数字始まり・連続ハイフン・末尾ハイフンは invalid
- グローバルデータベースインスタンスのマスターパスワードをコードや環境変数に書くと、 Secrets Manager に管理させない意味になる
- VPC セキュリティグループは `sg-` で始まる 8〜17 桁の 16 進数。形式チェックなしで渡すと CloudFormation や API が後で拒否する
- `MultiAZ=True` を指定すると高可用性が出るが、コストが約 2 倍になる。開発環境では既定 False

## Test

`examples/database-encrypted-instance_test.py`
