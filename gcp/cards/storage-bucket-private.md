---
id: storage-bucket-private
lang: gcp
title: 公開アクセスを禁止したオブジェクトストレージのバケットを作る
tags: [非公開バケット, 公開防止, 均一アクセス, 暗号化, cloud-storage, public-access-prevention, uniform-access, cmek]
lib: gcp.storage
fn: private_bucket_config
since: "2024"
verified: 2026-09-19
status: public
---

「誰にも公開せず、指定したサービスアカウントだけが読めるバケット」という要求から、`create_bucket` に渡すプロパティと `set_iam_policy` に渡す IAM ポリシーを組み立てる。

## Signature

```python
def private_bucket_config(name: str, location: str, *, project: str, kms_key_name: str | None = None, reader_members: Sequence[str] = (), labels: Mapping[str, str] | None = None, retention_period_seconds: int | None = None) -> dict[str, Any]
```

## Usage

```python
from google.cloud.storage import Bucket
from google.api_core.iam import Policy

out = private_bucket_config("example-bucket", "asia-northeast1", project="my-project")
bucket = Bucket(client, out["bucket"]["name"])
bucket._properties.update(out["bucket"])  # 公開防止・均一アクセス・版管理を作成前に載せる
client.create_bucket(bucket, location=out["bucket"]["location"])
bucket.set_iam_policy(Policy.from_api_repr(out["iam_policy"]))
```

## Contract

- `iamConfiguration.publicAccessPrevention` は `"enforced"`。組織ポリシーに関係なくバケット単位で公開を禁じる
- `iamConfiguration.uniformBucketLevelAccess.enabled` は `True`。ACL を無効にして IAM だけで権限を決める
- `versioning.enabled` は既定で `True`（誤削除・上書きから守る）
- `reader_members` は `roles/storage.objectViewer` の binding 1 つにまとまる。重複は除かれ、渡した順序を保つ。1 つも渡さなければ `bindings` は空で、誰にも権限を与えない
- `allUsers` / `allAuthenticatedUsers` を渡すと `ValueError`。公開配信が要るなら `cdn-static-site` を使う
- `kms_key_name` を渡したときだけ `encryption.defaultKmsKeyName` が入る。渡さなければ Google 管理鍵で暗号化される（保存時暗号化は常に有効）
- `labels` はキー順に並べ替えて入る。`retention_period_seconds` は渡したときだけ `retentionPolicy.retentionPeriod` に入る。JSON API の int64 は文字列なので値も文字列
- 名前（3〜63 文字・小文字・`goog` を含まない）、プロジェクト ID、CMEK のフルパス、正の保持期間、メンバーの接頭辞（`user:` / `serviceAccount:` / `group:`）を検証し、違反は `ValueError`
- 返すのは Storage JSON API の Bucket リソース（キーは camelCase）と IAM ポリシーの dict。SDK のオブジェクトへ変換するのは呼び出し側の仕事
- 同じ入力に同じ出力を返し、引数の配列や辞書を変更しない。返り値は `json.dumps` できる

## Alternatives

- SDK ではなく Terraform で書くなら `terraform/modules/storage-bucket-private`（AWS 版。GCP 版の module は未作成）
- AWS の同じ ID は `aws/examples/storage-bucket-private.py`（S3 の公開ブロックと SSE）
- 組織全体で公開を禁じるなら組織ポリシー `constraints/storage.publicAccessPrevention`。バケット単位の設定と併用できる

## Pitfalls

- バケット名は **プロジェクトではなくグローバルで一意**。他のプロジェクトが使っている名前は取れない
- 均一バケットレベルアクセスを有効にすると ACL の API が使えなくなる。既存バケットで切り替えると 90 日以内なら戻せるが、それ以降は戻せない
- `public_access_prevention` を `enforced` にしても、署名付き URL での配布は止まらない。止めたいなら鍵の発行側で制御する
- CMEK を使うときは、Cloud Storage のサービスエージェントに `roles/cloudkms.cryptoKeyEncrypterDecrypter` を与えておく必要がある（この関数は権限を作らない）
- `retention_policy` を lock するとオブジェクトを保持期間内に消せなくなる。この関数は lock しない

## Test

`examples/storage-bucket-private_test.py`
