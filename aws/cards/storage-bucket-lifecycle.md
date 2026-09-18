---
id: storage-bucket-lifecycle
lang: aws
title: バケットのオブジェクトを保持期間で自動的に移行・削除する
tags: [ライフサイクル, 保持期間, 移行, 削除, S3, lifecycle, retention, expiration]
lib: aws.s3
fn: lifecycle_rules
since: "2024"
verified: 2026-09-18
status: public
---

「N 日で安いストレージクラスへ移し、M 日で削除する」という保持要求から、boto3 の `put_bucket_lifecycle_configuration` に渡す `LifecycleConfiguration` を組み立てる。

## Signature

```python
def lifecycle_rules(transition_days: int | None, expiration_days: int | None, noncurrent_days: int | None, abort_multipart_days: int | None, prefix: str = "", storage_class: str = "STANDARD_IA") -> dict[str, Any]
```

## Usage

```python
import boto3
from storage_bucket_lifecycle import lifecycle_rules  # examples/storage-bucket-lifecycle.py をコピー

cfg = lifecycle_rules(transition_days=30, expiration_days=365, noncurrent_days=90, abort_multipart_days=7, prefix="logs/")
# cfg["Rules"][0] == {"ID": "lifecycle-logs/", "Filter": {"Prefix": "logs/"}, "Status": "Enabled",
#   "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}], "Expiration": {"Days": 365},
#   "NoncurrentVersionExpiration": {"NoncurrentDays": 90}, "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}}
boto3.client("s3").put_bucket_lifecycle_configuration(Bucket="example-bucket", LifecycleConfiguration=cfg)
```

## Contract

- ルールは常に 1 つ、`Status: Enabled`、`Filter: {"Prefix": prefix}`。`prefix` が `""` なら全オブジェクトが対象で `ID` は `lifecycle`、それ以外は `lifecycle-<prefix>`
- `transition_days` → `Transitions[0]` (`Days` + `StorageClass`)、`expiration_days` → `Expiration.Days`、`noncurrent_days` → `NoncurrentVersionExpiration.NoncurrentDays`、`abort_multipart_days` → `AbortIncompleteMultipartUpload.DaysAfterInitiation`。`None` を渡した項目はルールに含まれない
- `storage_class` は `STANDARD_IA`（既定）/ `ONEZONE_IA` / `INTELLIGENT_TIERING` / `GLACIER_IR` / `GLACIER` / `DEEP_ARCHIVE` のいずれか
- 同じ入力に同じ出力を返し、`json.dumps` できる
- `ValueError`: 日数が 1 未満・`int` でない（`bool` や小数も不可）、4 つとも `None`、`transition_days >= expiration_days`、`STANDARD_IA` / `ONEZONE_IA` への移行が 30 日未満、未知の `storage_class`

## Alternatives

- Terraform module `terraform/modules/storage-bucket-lifecycle`（同じ id。`aws_s3_bucket_lifecycle_configuration`）
- CloudFormation `AWS::S3::Bucket` の `LifecycleConfiguration.Rules`
- アクセスパターンが読めないなら `INTELLIGENT_TIERING` へ 0 日で移行し、階層間の移動は S3 に任せる（監視料が別途かかる）
- 削除ではなく「一定期間は削除できない」が要求なら Object Lock（バケット作成時にのみ有効化できる）

## Pitfalls

- `put_bucket_lifecycle_configuration` は**設定全体を置き換える**。既存ルールがあるバケットでは `get_bucket_lifecycle_configuration` で取り出して `Rules` を結合してから渡す
- 移行や削除は日単位で、UTC の 0 時にまとめて実行される。指定日ちょうどには起きない
- `NoncurrentVersionExpiration` はバージョニングが有効なバケットでしか意味がない（storage-object-versioning）。有効にしていないと非現行バージョンは存在しない
- `Expiration` はバージョニング有効なバケットでは削除マーカーを置くだけで、実体は `NoncurrentVersionExpiration` で消える。両方指定しないとストレージ料金が減らない
- `GLACIER` / `DEEP_ARCHIVE` は最低保存期間（90 / 180 日）があり、それより早く削除すると残り日数分が課金される。`expiration_days` は移行後の最低保存期間より後にする
- 128 KB 未満のオブジェクトは `STANDARD_IA` / `INTELLIGENT_TIERING` へ既定では移行されない

## Test

`examples/storage-bucket-lifecycle_test.py`
