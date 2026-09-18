---
id: database-backup-retention
lang: gcp
title: データベースの自動バックアップと保持期間を設定する
tags: [CloudSQL, 自動バックアップ, ポイントインタイム復旧, 世代数, cloud-sql, backup, pitr, retention]
lib: gcp.sql
fn: backup_retention_config
since: "2024"
verified: 2026-09-19
status: public
---

「毎日バックアップを取り、任意の時点へ戻せるようにする」という要求から Cloud SQL のバックアップ設定を組み立てる。API は呼ばない。

## Signature

```python
def backup_retention_config(*, start_time: str = '18:00', retained_backups: int = 30, point_in_time_recovery: bool = True, transaction_log_retention_days: int = 7, location: str | None = None) -> dict
```

## Usage

```python
cfg = backup_retention_config(retained_backups=60)
service.instances().patch(
    project="my-project", instance="example-db",
    body={"settings": {"backupConfiguration": cfg}},
).execute()
```

## Contract

- `enabled` は常に `True`。開始時刻は UTC の `"HH:MM"`
- 保持は日数ではなく世代数。`retentionUnit` は `"COUNT"`
- `point_in_time_recovery=False` のとき `transactionLogRetentionDays` のキー自体が入らない。無効にしつつログ保持日数を変えようとすると `ValueError`
- `location` は渡したときだけ入る
- `ValueError`: 開始時刻が 24 時間表記の `HH:MM` でない、保持数が 7〜365 の外、ログ保持日数が 1〜7 の外
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/database-backup-retention.py` — RDS の保持期間とバックアップウィンドウ
- `azure/examples/database-backup-retention.py` — 自動バックアップと長期保持
- 保持義務が長いならバックアップではなく、エクスポートをバケットに置いて `storage-bucket-lifecycle` で管理する
- 読み取り負荷を逃がすのが目的ならバックアップではなくリードレプリカを使う

## Pitfalls

- 開始時刻は UTC。日本時間で夜間にしたいつもりが日中になることがある
- 保持は世代数なので、バックアップが失敗した日が続くと実際に戻せる期間が短くなる
- ポイントインタイム復旧を有効にするとトランザクションログの保管ぶん費用が増える。ログ保持日数で調整する
- ログ保持の上限はエディションで変わる。Enterprise は 7 日まで。Enterprise Plus なら 35 日まで伸ばせるので、その場合はこの関数の上限を緩める
- 復元は新しいインスタンスとして作られる。元のインスタンスに上書きはできず、接続先が変わる
- バックアップの保存先を別の多リージョンにすると、復元先のリージョンに制限がかかることがある

## Test

`examples/database-backup-retention_test.py`
