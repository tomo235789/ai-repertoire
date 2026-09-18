---
id: secret-rotation
lang: aws
title: 秘密情報を定期的に自動ローテーションする
tags: [ローテーション, 定期更新, Secrets Manager, Lambda, rotation, schedule, auto-update]
lib: aws.secretsmanager
fn: rotation_config
since: "2024"
verified: 2026-09-18
status: public
---

「シークレットの秘密値を Lambda で定期的に自動更新する」という要求から、`rotate_secret` に渡す kwargs を組み立てる。ScheduleExpression は rate 式で表す。

## Signature

```python
def rotation_config(secret_id: str, rotation_lambda_arn: str, days: int, rotate_immediately: bool = False) -> dict[str, Any]
```

## Usage

```python
from secret_rotation import rotation_config  # examples/secret-rotation.py をコピー

out = rotation_config("app/prod/db", "arn:aws:lambda:us-east-1:123456789012:function:rotate-db-secret", 30)
sm.rotate_secret(**out)  # rate(30 days) で每月、RotateImmediately=False（次回スケジュールまで待つ）
```

## Contract

- `RotationRules.ScheduleExpression` は `rate({days} day)` （1 のとき単数形）、`rate({days} days)` （2 以上）の rate 式
- `RotateImmediately` は既定 `False`。True で設定と同時に 1 回ローテーションする
- `AutomaticallyAfterDays` は出力に含まない（ScheduleExpression と排他）
- 同じ入力に同じ出力を返し、入力を不変。全体を `json.dumps` できる
- `ValueError`: secret_id が空、Lambda ARN 形式外（`arn:aws:lambda:<region>:<account>:function:<name>`）、days が 1〜365 の範囲外
- `TypeError`: days が bool や int 以外

## Alternatives

- Terraform module `terraform/modules/secret-rotation`（同じ id。`aws_secretsmanager_secret_rotation` を同じ既定値で）
- CloudFormation `AWS::SecretsManager::RotationSchedule`。スケジュールは cron 式も使えるが、rate 式の制約がないため範囲検査は自前で行う

## Pitfalls

- Lambda の関数名 ARN はリージョン付き。ローテーション用 Lambda が別のリージョンにある場合、ARN の region を正しく指定する
- `rotate_secret` はシークレットの存在をチェックしない。存在しなくても CloudWatch に出ないことがある
- ローテーション間隔は AWS の上限が 365 日。それ以上の更新頻度は手動または EventBridge + Lambda で代替する

## Test

`examples/secret-rotation_test.py`
