---
id: secret-kms-key
lang: aws
title: 顧客管理の暗号鍵を作って保存データを暗号化する
tags: [CMK, 対称鍵, KMS, キーポリシー, 管理者分離, 自動ローテーション, symmetric-key, key-policy]
lib: aws.kms
fn: customer_managed_key
since: "2024"
verified: 2026-09-18
status: public
---

「管理者と利用者を分けた顧客管理の対称 CMK を作り、自動ローテーションと安全な削除予約を付ける」という要求から、`create_key` / `create_alias` / `enable_key_rotation` / `schedule_key_deletion` の kwargs を組み立てる。KeyId は後で作成されるため `KEY_ID_PLACEHOLDER` で繋ぐ。

## Signature

```python
def customer_managed_key(alias: str, admin_principal_arns: Sequence[str], user_principal_arns: Sequence[str], account_id: str, pending_window_days: int = 30, *, root_full_access: bool = True, description: str | None = None, tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from secret_kms_key import customer_managed_key  # examples/secret-kms-key.py をコピー

out = customer_managed_key("alias/app-data", [admin], [user], "123456789012", description="app data")
kms.create_key(**out["create_key"])           # Policy に管理者・利用者の分離文が含む
kms.create_alias(**out["create_alias"])       # TargetKeyId="{KeyId}"（作成後に置き換える）
kms.enable_key_rotation(**out["enable_key_rotation"])  # RotationPeriodInDays=365
kms.schedule_key_deletion(**out["schedule_key_deletion"])  # PendingWindowInDays=30
```

## Contract

- キーポリシーは `EnableRootAccountAccess`（root に kms:*）+ `AllowKeyAdministration`（管理者に管理アクションのみのリスト）+ `AllowKeyUsage`（利用者に暗号化・復号のみに限定）+ `AllowGrantsForAwsResources`（AWS サービス用 Gra nt 限定）の文から構成される
- 管理者のアクションには kms:Create*, Describe*, Enable*, List*, Put*, Update*, Revoke*, Disable*, Get*, Delete*, TagResource, UntagResource, ScheduleKeyDeletion, CancelKeyDeletion が含まれる。暗号化・復号は含まない
- 利用者のアクションには kms:Encrypt, Decrypt, ReEncrypt*, GenerateDataKey*, DescribeKey のみ。ポリシー変更や削除予約のアクションは含まない
- `AllowGrantsForAwsResources` は `kms:GrantIsForAWSResource: true` という Bool 条件付き
- `KeySpec: SYMMETRIC_DEFAULT`, `MultiRegion: False`, `BypassPolicyLockoutSafetyCheck: False`。既定で安全な値が固定される
- `root_full_access=False` のとき root 文が消え、その代わりに `admin_principal_arns` が空なら ValueError
- `pending_window_days` は 7〜30 のみ許容。範囲外は ValueError、int 以外は TypeError
- `alias/aws/` で始まるエイリアスは予約語で不可

## Alternatives

- Terraform resource `terraform/modules/secret-kms-key`（同じ id。`aws_kms_key` + `aws_kms_alias` を同じ既定値で）
- CloudFormation `AWS::KMS::Key` の `KeyPolicy` プロパティ。エイリアスは `AWS::KMS::Alias` 別リソース

## Pitfalls

- create_key の返す KeyId は実行時に決まるため、後続の API に渡すには `{KeyId}` プレースホルダーを埋めて置換する（CloudFormation の Fn:GetAtt / Terraform の ${aws_kms_key.x.key_id}）
- キーポリシーの文は json.dumps してから create_key に渡す。 boto3 は dict をそのまま受け取る
- `root_full_access=False` で admin_principal_arns も空にすると、誰も管理できない鍵が作られる（バッチリ防止）
- `alias/` のプレフィックスは必須。aws/ プレフィックスは AWS 管理キー用で Reserved

## Test

`examples/secret-kms-key_test.py`
