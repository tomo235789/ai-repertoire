---
id: storage-bucket-private
lang: aws
title: 公開アクセスを禁止したオブジェクトストレージのバケットを作る
tags: [バケット, 非公開, 暗号化, S3, bucket, private, encryption, public-access-block]
lib: aws.s3
fn: private_bucket_config
since: "2024"
verified: 2026-09-18
status: public
---

「誰にも公開しない、保存時に暗号化された S3 バケット」という要求から、boto3 の `create_bucket` / `put_public_access_block` / `put_bucket_encryption` / `put_bucket_ownership_controls` / `put_bucket_policy` に渡す設定を組み立てる。

## Signature

```python
def private_bucket_config(name: str, kms_key_id: str | None = None, tags: Mapping[str, str] | None = None, region: str | None = None) -> dict[str, Any]
```

## Usage

```python
import json
import boto3
from storage_bucket_private import private_bucket_config  # examples/storage-bucket-private.py をコピー

cfg = private_bucket_config("example-bucket", tags={"env": "dev"})
s3 = boto3.client("s3", region_name="us-east-1")
s3.create_bucket(**cfg["create_bucket"])                    # ObjectOwnership=BucketOwnerEnforced（ACL 無効）
s3.put_public_access_block(**cfg["public_access_block"])   # 4 つの Block/Ignore/Restrict がすべて True
s3.put_bucket_encryption(**cfg["encryption"])              # kms_key_id 無しなら SSE-S3（AES256）
s3.put_bucket_policy(Bucket="example-bucket", Policy=json.dumps(cfg["policy"]))  # HTTP を Deny
```

## Contract

- `public_access_block` は `BlockPublicAcls` / `IgnorePublicAcls` / `BlockPublicPolicy` / `RestrictPublicBuckets` の 4 つがすべて `True`
- `create_bucket` と `ownership` はどちらも `BucketOwnerEnforced`（ACL 無効。オブジェクトはすべてバケット所有者のもの）
- `encryption` は `kms_key_id` 無しで `SSEAlgorithm: AES256`（SSE-S3）、有りで `aws:kms` + `KMSMasterKeyID` + `BucketKeyEnabled: True`
- `policy` は `Deny` 文 1 つだけ（`Allow` は含まない）。`aws:SecureTransport` が `false` の全 `s3:*` をバケットとオブジェクト両方の ARN で拒否する
- `tags` を渡すとキー順にソートした `tagging.Tagging.TagSet` を返す。空か `None` なら `tagging` キー自体が無い
- `region` が `us-east-1` 以外なら `create_bucket` に `CreateBucketConfiguration.LocationConstraint` を付ける。`us-east-1` と未指定では付けない
- 同じ入力に同じ出力を返し、入力の `tags` を変更しない。全体を `json.dumps` できる
- `ValueError`: S3 の命名規則に反する名前（大文字・`_`・3 文字未満・64 文字以上・先頭末尾の `-` `.`・`..`・IPv4 形式）、空白だけの `kms_key_id`、タグが 51 個以上かキー 129 文字超・値 257 文字超

## Alternatives

- Terraform module `terraform/modules/storage-bucket-private`（同じ id。`aws_s3_bucket_public_access_block` + `aws_s3_bucket_server_side_encryption_configuration` を同じ既定値で）
- CloudFormation `AWS::S3::Bucket` の `PublicAccessBlockConfiguration` / `BucketEncryption` / `OwnershipControls` プロパティ。バケットポリシーは別リソース `AWS::S3::BucketPolicy`
- アカウント全体で公開を禁止するなら `s3control.put_public_access_block(AccountId=...)`。バケット単位の設定より優先される

## Pitfalls

- `policy` は dict。`put_bucket_policy` の `Policy` は JSON 文字列なので `json.dumps` してから渡す
- バケット名はグローバルに一意。他アカウントが使っている名前は `BucketAlreadyExists` になる。ドット入りの名前は `https://<bucket>.s3.amazonaws.com` の TLS 証明書と合わないので避ける
- `create_bucket` はリージョン依存。`us-east-1` 以外のクライアントで `LocationConstraint` 無しに呼ぶと `IllegalLocationConstraintException`。クライアントの `region_name` と `region` 引数を揃える
- 5 つの API は順に呼ぶ必要があり、途中で失敗するとバケットだけ残る。put 系は冪等なので再実行してよいが、`create_bucket` は 2 回目に `BucketAlreadyOwnedByYou` を返す（`us-east-1` だけは成功扱い）ので握りつぶす
- KMS 鍵を使うと、読み書きするロールに `kms:Decrypt` / `kms:GenerateDataKey` も必要になる。バケットポリシーではなく鍵ポリシーと IAM で許可する
- 公開ブロックが有効でも、同一アカウント内の IAM ユーザーには影響しない。アクセス制御は IAM とバケットポリシーで別途行う

## Test

`examples/storage-bucket-private_test.py`
