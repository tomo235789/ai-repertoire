---
id: database-read-replica
lang: aws
title: 読み取り負荷を分散するリードレプリカを作る
tags: [リーダブル, リーダレプリカ, RDS, クロスリージョン, スケーリング, read-replica, replication, rds]
lib: aws.rds
fn: read_replica
since: "2024"
verified: 2026-09-18
status: public
---

同一リージョン / クロスリージョンの両パターンに対応したリードレプリカを、rds.create_db_instance_read_replica の kwargs として組み立てる。ソースを ARN で指定するとクロスリージョン扱いになる。

## Signature

```python
def read_replica(identifier: str, source_identifier_or_arn: str, instance_class: str, kms_key_id: str | None = None, *, subnet_group: str | None = None, security_group_ids: Sequence[str] | None = None, tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from database_read_replica import read_replica  # examples/database-read-replica.py をコピー

# 同一リージョン（識別子指定）
kw = read_replica("app-db-ro", "app-db", "db.t4g.micro")
client.create_db_instance_read_replica(**kw)  # SourceRegion / KmsKeyId は出力に含まれない

# クロスリージョン（ARN 指定）
kw_xr = read_replica("app-db-ro-west", SOURCE_ARN, "db.t4g.micro", KEY_WEST, subnet_group="private-west")
# SourceRegion: "us-east-1" / KmsKeyId が追加される
```

## Contract

- `SourceDBInstanceIdentifier` にそのまま `source_identifier_or_arn` を入れる（識別子でも ARN でも同じキー）
- 同一リージョン（識別子指定）では `KmsKeyId` / `SourceRegion` を出力に含まない。レプリカはソースと同じ鍵で暗号化される
- クロスリージョン（ARN 指定）では `SourceRegion` を ARN から抽出して入れる。`kms_key_id` と `subnet_group` が必須になる
- `PubliclyAccessible` はどちらの形でも `False`。`AutoMinorVersionUpgrade` / `CopyTagsToSnapshot` は `True`
- source の識別子とレプリカの識別子が同じなら ValueError（ループ防止）
- ARN 形式は `arn:aws:rds:<region>:<account>:db:<id>` のみに制限。クラスター ARN は拒否
- 同じ入力に同じ出力を返し、入力を変更しない。全体を `json.dumps` できる

## Alternatives

- Terraform module `terraform/modules/database-read-replica`（同じ id。`aws_db_instance` の `replicate_source_db` を同一リージョン/クロスリージョンで使い分ける）
- CloudFormation `AWS::RDS::DBInstance` の `ReadReplicaSourceDBInstanceIdentifier` / `SourceRegion` プロパティ

## Pitfalls

- クロスリージョンレプリカではレプリカ側リージョンの CMK が必須。ソース側の鍵は使えない（異なる KMS サービス間）
- CloudFormation ではクロスリージョンレプリカ作成が制限されている（CloudFormation は単一リージョンのリソース管理が前提）。boto3 API で作成する必要がある
- `SecurityGroupIds` を指定しないとソースと同じセキュリティグループになる（同一リージョン限定）。クロスリージョンで未指定だとデフォルト VPC に置かれる

## Test

`examples/database-read-replica_test.py`
