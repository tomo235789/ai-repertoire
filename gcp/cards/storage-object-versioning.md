---
id: storage-object-versioning
lang: gcp
title: バケットのオブジェクトをバージョン管理して誤削除から守る
tags: [バージョニング, 論理削除, 旧版, 保持ポリシー, versioning, soft-delete, noncurrent, retention-policy]
lib: gcp.storage
fn: versioning_config
since: "2024"
verified: 2026-09-19
status: public
---

「上書きしても消しても戻せる。ただし旧版は溜めすぎない」という要求からバケットのプロパティとライフサイクル規則を組み立てる。API は呼ばない。

## Signature

```python
def versioning_config(*, keep_newer_versions: int = 3, delete_noncurrent_after_days: int = 30, soft_delete_retention_days: int = 7, retention_period_seconds: int | None = None) -> dict
```

## Usage

```python
cfg = versioning_config(keep_newer_versions=5)
bucket = client.bucket("example-bucket")
bucket._properties.update(cfg["properties"])  # 版管理・論理削除・保持を一度に載せる
bucket.lifecycle_rules = cfg["lifecycle_rules"]
bucket.patch()
```

## Contract

- `versioning.enabled` は常に `True`
- 論理削除の保持は秒で渡す。`soft_delete_retention_days` を 86400 倍した値が入る。JSON API の int64 は文字列なので値も文字列
- ライフサイクル規則は 1 本。旧版を `daysSinceNoncurrentTime` と `numNewerVersions` の両方の条件で消す
- `retentionPolicy` は `retention_period_seconds` を渡したときだけ入る。値は文字列
- `ValueError`: 残す版の数が 1 未満、旧版の削除日数が 1 未満、論理削除の保持日数が 7〜90 の外、保持期間が 1 秒未満
- 返すのは Storage JSON API のプロパティ。SDK のオブジェクトへ載せるのは呼び出し側の仕事
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/storage-object-versioning.py` — S3 のバージョニング
- `azure/examples/storage-object-versioning.py` — Blob のバージョン管理とポイントインタイム復元
- 版を残さず期間で消すだけなら `storage-bucket-lifecycle` を使う
- 改変そのものを禁じたいならバケットロックで保持ポリシーを固定する

## Pitfalls

- 版管理を有効にすると、上書きのたびに旧版が課金対象として残る。ライフサイクル規則とセットで使う
- 論理削除はバケットの既定で有効になっている。無効にすると削除の取り消しができない
- 保持ポリシーを設定すると、期間内はライフサイクル規則でも消せない。試験環境で固めると消せなくて困る
- バケットロックをかけた保持ポリシーは、期間を延ばせても縮められない。取り消せない
- 旧版の一覧は既定の `list_blobs` には出てこない。`versions=True` が要る

## Test

`examples/storage-object-versioning_test.py`
