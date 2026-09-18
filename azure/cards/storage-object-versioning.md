---
id: storage-object-versioning
lang: azure
title: バケットのオブジェクトをバージョン管理して誤削除から守る
tags: [バージョン管理, 論理削除, 変更フィード, 復元, versioning, soft-delete, change-feed, point-in-time-restore]
lib: azure.storage
fn: versioning_config
since: "2024"
verified: 2026-09-19
status: public
---

「上書きしても消しても元に戻せるようにする」という要求から Blob サービスのプロパティを組み立てる。API は呼ばない。

## Signature

```python
def versioning_config(*, blob_retention_days: int = 30, container_retention_days: int = 30, point_in_time_restore_days: int | None = None) -> dict
```

## Usage

```python
props = versioning_config(point_in_time_restore_days=7)
client.blob_services.set_service_properties(
    "example-rg", "examplestorage", props
)
```

## Contract

- `isVersioningEnabled` は常に `True`
- Blob とコンテナの論理削除は常に有効で、保持日数は引数で決まる。既定は両方 30 日
- `allowPermanentDelete` は常に `False`。保持期間中の版を消せなくする
- `changeFeed` は常に有効。ポイントインタイム復元の前提になる
- `restorePolicy` は既定で `{"enabled": False}`。`point_in_time_restore_days` を渡すと有効になる
- `ValueError`: 保持日数が 1〜365 の外、復元日数が 1 未満、復元日数が `blob_retention_days` 以上
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/storage-object-versioning.py` — S3 のバージョニングと MFA Delete
- `gcp/examples/storage-object-versioning.py` — オブジェクトのバージョニングと世代数の制限
- 版を残さず古いものを消したいだけなら `storage-bucket-lifecycle` を使う
- 規制対応で改変そのものを禁じたいなら不変ストレージ（法的保持・時間ベース保持）を使う

## Pitfalls

- バージョン管理を有効にすると、上書きのたびに前の版が課金対象として残る。`storage-bucket-lifecycle` の `version` ルールで古い版を消す
- ポイントインタイム復元は変更フィードとバージョン管理と論理削除がすべて要る。どれかが欠けると設定が拒否される
- 復元できる期間は論理削除の保持日数より**短く**しなければならない。同じ日数にすると作成に失敗する
- 論理削除は削除を取り消せるだけで、アカウントごと消されたら戻せない。別リージョンへのレプリケーションは別の話
- 変更フィードは有効にした時点から記録される。過去にさかのぼって復元することはできない

## Test

`examples/storage-object-versioning_test.py`
