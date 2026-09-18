---
id: database-backup-retention
lang: aws
title: データベースの自動バックアップと保持期間を設定する
tags: [バックアップ, 保持期間, RDS, ウィンドウ, snapshot, backup, retention-window, rds]
lib: aws.rds
fn: backup_settings
since: "2024"
verified: 2026-09-18
status: public
---

RDS インスタンスの自動バックアップ保持期間とバックアップウィンドウを、rds.modify_db_instance（create_db_instance でも同じキー）に渡す kwargs として組み立てる。retention_days=0 はこの関数では作れない。

## Signature

```python
def backup_settings(retention_days: int, backup_window: str | None = None, copy_tags: bool = True) -> dict[str, Any]
```

## Usage

```python
from database_backup_retention import backup_settings  # examples/database-backup-retention.py をコピー

kw = backup_settings(7, "17:00-17:30")  # 保持 7 日・UTC 17:00〜17:30 にバックアップ
client.modify_db_instance(DBInstanceIdentifier="app-db", **kw)
# DBInstanceIdentifier と ApplyImmediately は呼び出し側が渡す（出力に含まない）
```

## Contract

- `BackupRetentionPeriod` は `retention_days` そのもの（1〜35）。0 は受け付けない（自動バックアップの無効化を誤設定から防ぐ）
- `PreferredBackupWindow` は UTC の `hh24:mi-hh24:mi` 形式。日付を跨ぐ指定（例: `"23:45-00:15"`）も許可。30 分未満は拒否
- `copy_tags=True`（既定）で `CopyTagsToSnapshot` が `True`。False を渡すと出力にも反映される
- window 未指定なら `PreferredBackupWindow` キーを出力に含まない（AWS のリージョン既定枠に任せる）
- `retention_days` は bool / float / int 以外を受け付けない。36 と負数は ValueError
- `DBInstanceIdentifier` / `ApplyImmediately` を出力に含めない。呼び出し側が決める

## Alternatives

- Terraform module `terraform/modules/database-backup-retention`（同じ id。`aws_db_instance` の `backup_retention_period` + `preferred_backup_window`）
- CloudFormation `AWS::RDS::DBInstance` の `BackupRetentionPeriod` / `PreferredBackupWindow` プロパティ

## Pitfalls

- バックアップウィンドウは UTC で指定する。日本から `09:00-09:30` と書いても UTC 09:00（JST 18:00）になる
- `retention_days=0` は「自動バックアップを無効化」を意味する。この関数では意図的な誤設定防止のために拒否している
- `modify_db_instance` に渡す場合、変更は即座に反映される（`ApplyImmediately=True` 既定）。バッチ実行中にバックアップが走ると一時的に IO が止まる

## Test

`examples/database-backup-retention_test.py`
