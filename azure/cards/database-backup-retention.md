---
id: database-backup-retention
lang: azure
title: データベースの自動バックアップと保持期間を設定する
tags: [バックアップ, 保持期間, 長期保持, 地理冗長, backup, retention, long-term-retention, geo-redundant]
lib: azure.sql
fn: backup_retention_config
since: "2024"
verified: 2026-09-19
status: public
---

「直近は日単位で戻せて、年次のものは数年残す」という要求から、自動バックアップと長期保持の設定を組み立てる。API は呼ばない。

## Signature

```python
def backup_retention_config(*, retention_days: int = 35, geo_redundant: bool = True, weekly_retention_weeks: int | None = None, monthly_retention_months: int | None = None, yearly_retention_years: int | None = None, week_of_year_for_yearly: int = 1) -> dict
```

## Usage

```python
cfg = backup_retention_config(weekly_retention_weeks=12, yearly_retention_years=5)
client.servers.begin_update(
    "example-rg", "example-db", {"properties": {"backup": cfg["backup_on_update"]}}
).result()
# 長期保持はサーバー更新では効かない。Azure Backup / SQL の別 API に渡す
apply_long_term_retention(cfg["long_term_retention"])
```

## Contract

- 自動バックアップの保持日数は 7〜35 日。既定は 35 日で、地理冗長は既定で有効
- 長期保持は ISO 8601 の duration。使わない期間は `"PT0S"` になる
- `backup_on_create` は作成時の body。地理冗長は作成時にしか決められないので、`backup_on_update` には入らない
- `long_term_retention` はサーバーの作成にも更新にも渡せない。Azure SQL Database なら `backupLongTermRetentionPolicies`、PostgreSQL フレキシブルサーバーなら Azure Backup のポリシーで設定する
- 年次保持を指定しないと `weekOfYear` は `0` に落ちる
- 週次の長期保持は自動バックアップの保持期間より長くする。短いと `ValueError`
- `ValueError`: 保持日数が 7〜35 の外、週次が 1〜520 の外、月次が 1〜120 の外、年次が 1〜10 の外、週番号が 1〜52 の外
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/database-backup-retention.py` — RDS の保持期間とバックアップウィンドウ
- `gcp/examples/database-backup-retention.py` — Cloud SQL の自動バックアップとポイントインタイム復旧
- 論理的な誤りからの復旧が目的なら、バックアップより先に `storage-object-versioning` のような版管理を検討する
- 別リージョンで即座に読めるようにしたいならバックアップではなくリードレプリカを使う

## Pitfalls

- 地理冗長バックアップはサーバー作成時にしか決められない。更新の body に入れると、無効で作ったサーバーでは拒否される
- 保持期間を縮めると、その期間より古い復元ポイントはすぐに消える。戻せなくなる
- 長期保持のバックアップは自動バックアップとは別に課金される。年次を 10 年残すと積み上がる
- 復元は新しいサーバーとして作られる。元のサーバーに上書きはできず、接続文字列も変わる
- ポイントインタイム復元は保持期間の範囲でしかできない。長期保持のバックアップは指定した時点のものだけ

## Test

`examples/database-backup-retention_test.py`
