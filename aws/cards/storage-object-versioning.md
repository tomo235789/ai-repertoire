---
id: storage-object-versioning
lang: aws
title: バケットのオブジェクトをバージョン管理して誤削除から守る
tags: [バージョニング, 誤削除, 復元, S3, versioning, MFA delete, recovery]
lib: aws.s3
fn: versioning_config
since: "2024"
verified: 2026-09-18
status: public
---

「上書きや削除をしても前の版に戻せるようにしたい」という要求から、boto3 の `put_bucket_versioning` に渡す `VersioningConfiguration` を組み立てる。

## Signature

```python
def versioning_config(enabled: bool = True, mfa_delete: bool = False) -> dict[str, str]
```

## Usage

```python
import boto3
from storage_object_versioning import versioning_config  # examples/storage-object-versioning.py をコピー

cfg = versioning_config()            # {"Status": "Enabled"}
boto3.client("s3").put_bucket_versioning(Bucket="example-bucket", VersioningConfiguration=cfg)

versioning_config(enabled=False)     # {"Status": "Suspended"}（Disabled には戻せない）
versioning_config(mfa_delete=True)   # {"Status": "Enabled", "MFADelete": "Enabled"}（MFA ヘッダとルート資格情報が必要）
```

## Contract

- 既定（引数なし）は `{"Status": "Enabled"}` だけ。`MFADelete` キーは付かない
- `enabled=False` は `Status: Suspended`。`Disabled` は決して出力しない（一度有効にしたバケットは戻せない）
- `mfa_delete=True` のときだけ `MFADelete: Enabled` を付ける。`Suspended` との組み合わせも可
- 同じ入力に同じ出力を返し、`json.dumps` できる
- `ValueError` を投げる条件は無い（引数は 2 つの真偽値のみ）

## Alternatives

- Terraform module `terraform/modules/storage-object-versioning`（同じ id。`aws_s3_bucket_versioning`）
- CloudFormation `AWS::S3::Bucket` の `VersioningConfiguration: {Status: Enabled}`
- 削除そのものを法的に禁止する要求なら Object Lock（バージョニングが前提。バケット作成時に有効化）
- 別リージョン・別アカウントへの複製で守るなら S3 Replication（これもバージョニングが前提）

## Pitfalls

- `MFADelete` を含む設定は `put_bucket_versioning(..., MFA="<serial> <code>")` を付け、**ルートユーザーの資格情報**で呼ぶ必要がある。IAM ユーザー / ロールからは設定できない。この関数は MFA コードを扱わない（時刻依存の値なので呼び出し側で渡す）
- バージョニングを有効にすると、削除は「削除マーカーの追加」になり、古い版は課金され続ける。storage-bucket-lifecycle の `noncurrent_days` で非現行バージョンを消す設定を必ず組み合わせる
- `Suspended` にしても既存のバージョンは残る。以後の上書きは `null` バージョン ID のオブジェクトを置き換える
- 有効化前に置いたオブジェクトはバージョン ID が `null` になり、`list_object_versions` では `null` として見える
- リージョンをまたぐ複製や Object Lock はバージョニングが有効でないと設定できない。順序: 作成 → バージョニング → 複製 / Lock

## Test

`examples/storage-object-versioning_test.py`
