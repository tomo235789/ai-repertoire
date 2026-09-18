---
id: storage-bucket-lifecycle
lang: azure
title: バケットのオブジェクトを保持期間で自動的に移行・削除する
tags: [ライフサイクル, 階層化, アーカイブ, 保持期間, lifecycle, tiering, archive, retention]
lib: azure.storage
fn: lifecycle_policy
since: "2024"
verified: 2026-09-19
status: public
---

「30 日でクール、90 日でアーカイブ、1 年で削除」という要求から管理ポリシーのルールを組み立てる。API は呼ばない。

## Signature

```python
def lifecycle_policy(rule_name: str, *, prefix_match=(), days_to_cool: int | None = 30, days_to_archive: int | None = 90, days_to_delete: int | None = 365, delete_old_versions_after_days: int | None = 90, delete_snapshots_after_days: int | None = 90) -> dict
```

## Usage

```python
props = lifecycle_policy("archive-old", prefix_match=["logs/"])
client.management_policies.create_or_update(
    "example-rg", "examplestorage", "default", properties=props
)
```

## Contract

- ルールは 1 本。`enabled` は `True`、`type` は `"Lifecycle"`、対象は `blockBlob`
- `prefix_match` を省略するとアカウント内のすべての Blob が対象
- 基底 Blob の段階は**最終更新**からの日数、旧版とスナップショットは**作成**からの日数で判定する
- 段階に `None` を渡すとそのアクションはルールに入らない
- `ValueError`: ルール名が空、いずれかの日数が 1 未満、クール → アーカイブ → 削除の順序が逆転、移行も削除も何も指定しなかった場合
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/storage-bucket-lifecycle.py` — S3 のライフサイクル設定。ストレージクラス名が異なる
- `gcp/examples/storage-bucket-lifecycle.py` — ライフサイクル条件とアクション
- 消さずに版だけ整理したいなら `storage-object-versioning` と組み合わせ、`delete_old_versions_after_days` だけ設定する
- アクセス頻度で自動的に層を決めたいなら日数ではなくライフサイクル管理の最終アクセス時刻ベースの条件を使う

## Pitfalls

- 管理ポリシーの名前は `"default"` 固定。別名では作れない
- ルールの評価は 1 日 1 回程度。設定した瞬間に移行や削除が起きるわけではない
- アーカイブ層の Blob は読む前にリハイドレートが要り、数時間かかる。読み取り頻度がある対象をアーカイブに送らない
- アーカイブ層には最低保持期間があり、早く消すと早期削除料金がかかる
- プレミアムのブロック Blob アカウントはアーカイブ層に対応していない

## Test

`examples/storage-bucket-lifecycle_test.py`
