---
id: storage-bucket-lifecycle
lang: gcp
title: バケットのオブジェクトを保持期間で自動的に移行・削除する
tags: [ライフサイクル, ストレージクラス, 最低保存期間, 旧版, lifecycle, storage-class, minimum-duration, noncurrent]
lib: gcp.storage
fn: lifecycle_rules
since: "2024"
verified: 2026-09-19
status: public
---

「30 日で Nearline、90 日で Coldline、1 年で削除」という要求からライフサイクル規則を組み立てる。階層ごとの最低保存期間も検査する。API は呼ばない。

## Signature

```python
def lifecycle_rules(*, transitions: dict[str, int] | None = None, delete_after_days: int | None = 365, delete_noncurrent_after_days: int | None = 30, keep_newer_versions: int = 3, matches_prefix=()) -> list[dict]
```

## Usage

```python
bucket = client.bucket("example-bucket")
bucket.lifecycle_rules = lifecycle_rules(matches_prefix=["logs/"])
bucket.patch()
```

## Contract

- 移行規則は単価が下がる順（STANDARD → NEARLINE → COLDLINE → ARCHIVE）に並ぶ。入力の順序は問わない
- 削除規則は移行のあと、旧版の削除はその次に入る
- 旧版の削除条件には `daysSinceNoncurrentTime` と `numNewerVersions` の両方が入る
- `matches_prefix` を渡すとすべての規則の条件に付く
- `None` を渡した削除規則は作られない
- `ValueError`: 未知のストレージクラス、`STANDARD` への移行、日数が 1 未満、移行の順序の逆転、最後の移行以前の削除、最後の階層の最低保存期間を置かずに削除、残す版の数が負
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/storage-bucket-lifecycle.py` — S3 のライフサイクル設定
- `azure/examples/storage-bucket-lifecycle.py` — Blob の管理ポリシー
- 版だけ整理したいなら `storage-object-versioning` と合わせ、旧版の規則だけ使う
- 消さずに残す義務があるなら保持ポリシーとバケットロックを使う

## Pitfalls

- 階層には最低保存期間がある。Nearline は 30 日、Coldline は 90 日、Archive は 365 日。移行そのものは早くできるが、移行してからその期間より前に消すと差額が請求される。この関数は削除日数の側で検査する
- ライフサイクルの評価は 1 日 1 回程度。設定した瞬間には動かない
- 条件をひとつの規則に複数書くと AND になる。OR にしたいなら規則を分ける
- `numNewerVersions` を指定せずに旧版を消すと、最新版しか残らない状態になりうる
- バケットのライフサイクルはオブジェクト保持ポリシーより弱い。保持中のオブジェクトは削除規則があっても消えない

## Test

`examples/storage-bucket-lifecycle_test.py`
