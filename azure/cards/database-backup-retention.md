---
id: database-backup-retention
lang: azure
title: データベースの自動バックアップと保持期間を設定する
tags: [バックアップ, 保持期間, 地理冗長, 作成時のみ, backup, retention, geo-redundant, create-only]
lib: azure.sql
fn: backup_retention_config
since: "2024"
verified: 2026-09-19
status: public
---

「直近は日単位で戻せるようにする」という要求から、PostgreSQL フレキシブルサーバーの自動バックアップ設定を組み立てる。API は呼ばない。

## Signature

```python
def backup_retention_config(*, retention_days: int = 35, geo_redundant: bool = True) -> dict
```

## Usage

```python
cfg = backup_retention_config(retention_days=30)
client.servers.begin_update(
    "example-rg", "example-db", {"properties": {"backup": cfg["backup_on_update"]}}
).result()
```

## Contract

- `backup_on_create` はサーバー作成時の body。`backupRetentionDays` と `geoRedundantBackup` を持つ
- `backup_on_update` は既存サーバーの更新用。地理冗長は作成時にしか決められないので入らない
- `ValueError`: 保持日数が 7〜35 の外
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- 週次・月次・年次の長期保持は、サーバーのプロパティではなく Azure Backup のバックアップポリシーで設定する。スケジュールと保持ルールを持つ別のリソースなのでこのカードでは扱わない
- `aws/examples/database-backup-retention.py` — RDS の保持期間とバックアップウィンドウ
- `gcp/examples/database-backup-retention.py` — Cloud SQL の自動バックアップとポイントインタイム復旧
- 論理的な誤りからの復旧が目的なら、バックアップより先に `storage-object-versioning` のような版管理を検討する
- 別リージョンで即座に読めるようにしたいならバックアップではなくリードレプリカを使う

## Pitfalls

- 地理冗長バックアップはサーバー作成時にしか決められない。更新の body に入れると、無効で作ったサーバーでは拒否される
- 保持期間を縮めると、その期間より古い復元ポイントはすぐに消える。戻せなくなる
- 長期保持が要るなら Azure Backup のコンテナーとポリシーを別に作る。この関数の返り値では設定できない
- 復元は新しいサーバーとして作られる。元のサーバーに上書きはできず、接続文字列も変わる
- ポイントインタイム復元は保持期間の範囲でしかできない

## Test

`examples/database-backup-retention_test.py`
