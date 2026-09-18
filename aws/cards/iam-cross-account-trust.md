---
id: iam-cross-account-trust
lang: aws
title: 別アカウントからの引き受けを許可する信頼関係を作る
tags: [クロスアカウント, 信頼関係, ExternalId, 引き受け, IAM, cross-account, assume role, trust policy]
lib: aws.iam
fn: cross_account_trust
since: "2024"
verified: 2026-09-18
status: public
---

「別の AWS アカウント（監査、SaaS ベンダー、CI アカウントなど）からこのロールを引き受けさせたい」という要求から、`create_role` に渡す信頼ポリシーと `MaxSessionDuration` を組み立てる。`sts:ExternalId` 条件で混乱した代理を防ぐ。

## Signature

```python
def cross_account_trust(account_ids: Iterable[str], external_id: str, max_session_seconds: int = 3600, require_mfa: bool = False) -> dict[str, Any]
```

## Usage

```python
import json
import boto3
from iam_cross_account_trust import cross_account_trust  # examples/iam-cross-account-trust.py をコピー

cfg = cross_account_trust(["123456789012"], external_id="example-external-id", max_session_seconds=3600)
# cfg["assume_role_policy"]["Statement"][0]["Principal"] == {"AWS": ["arn:aws:iam::123456789012:root"]}
# ...["Condition"] == {"StringEquals": {"sts:ExternalId": "example-external-id"}, "NumericLessThanEqualsIfExists": {"sts:DurationSeconds": "3600"}}
boto3.client("iam").create_role(RoleName="example-audit", AssumeRolePolicyDocument=json.dumps(cfg["assume_role_policy"]),
                                MaxSessionDuration=cfg["max_session_duration"])
```

## Contract

- `assume_role_policy` は `Allow` 文 1 つ（`Sid: CrossAccountAssumeRole`）。`Principal.AWS` は各アカウントの `arn:aws:iam::<id>:root`（ソート・重複除去）、`Action = sts:AssumeRole`
- `Condition.StringEquals["sts:ExternalId"]` が**必ず**入る。省略できない
- `Condition.NumericLessThanEqualsIfExists["sts:DurationSeconds"]` に `max_session_seconds`（文字列）が入り、`max_session_duration` にも同じ値（int）を返す
- `require_mfa=True` のときだけ `Condition.Bool["aws:MultiFactorAuthPresent"] = "true"` が付く
- 同じ入力に同じ出力を返し、`json.dumps` できる
- `ValueError`: `account_ids` が空か 12 桁の数字以外（ARN 形式も不可）、`external_id` が 2〜1224 文字の `[A-Za-z0-9_+=,.@:/-]` に合わない、`max_session_seconds` が 3600〜43200 の `int` でない（`bool` や小数も不可）

## Alternatives

- Terraform module `terraform/modules/iam-cross-account-trust`（同じ id。`aws_iam_role` の `assume_role_policy`）
- CloudFormation `AWS::IAM::Role` の `AssumeRolePolicyDocument` + `MaxSessionDuration`
- 同一 Organization 内なら `Principal.AWS` に `root` を並べる代わりに `aws:PrincipalOrgID` 条件で組織単位に許可する方が管理しやすい
- 人間のクロスアカウント操作は IAM Identity Center（SSO）で。ExternalId は SaaS や自動化アカウントなど「第三者がロールを引き受ける」場面のためのもの

## Pitfalls

- `AssumeRolePolicyDocument` は JSON 文字列。`json.dumps` してから渡す
- `:root` を信頼すると、相手アカウントの**すべての IAM プリンシパル**が（相手側の IAM で許可されていれば）引き受けられる。特定のロールに絞るなら `arn:aws:iam::<id>:role/<name>` を渡す。ただし相手側でロールを作り直すと一意 ID が変わり、信頼ポリシー内の ARN が無効化される
- ExternalId は秘密ではなく識別子。推測されにくい値にはするが、これだけで認証にはならない。`require_mfa` は人間が引き受ける場合にだけ意味がある（ロールからロールの連鎖では MFA コンテキストが伝わらない）
- `MaxSessionDuration` は `create_role` / `update_role` の引数で、信頼ポリシーには入らない。返り値の両方を渡す。ポリシー側の `sts:DurationSeconds` 条件は `IfExists` なので、`DurationSeconds` を省略した引き受け（既定 1 時間）は通り、上限より長く要求した場合だけ拒否される。ロールの連鎖（ロールから別ロールを引き受ける）ではセッションは常に 1 時間が上限
- IAM の評価は「明示的 Deny > Allow」。相手アカウント側の IAM で `sts:AssumeRole` を許可し、自アカウントの SCP で拒否していないことも必要。片方だけでは引き受けられない
- 信頼ポリシーを更新するのは `update_assume_role_policy`。`create_role` を再実行しても `EntityAlreadyExists` で変わらない

## Test

`examples/iam-cross-account-trust_test.py`
