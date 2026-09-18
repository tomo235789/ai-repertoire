---
id: iam-cross-account-trust
lang: terraform
title: 別アカウントからの引き受けを許可する信頼関係を作る
tags: [クロスアカウント, 信頼関係, ExternalId, 混乱した代理, cross-account, assume-role, trust-policy, external-id]
lib: hashicorp/aws
fn: aws_iam_role
since: "5.0"
verified: 2026-09-18
status: public
---

「監視 SaaS や別部署のアカウントに、このアカウントのロールを引き受けさせたい」という要求に対する設定。principal を ARN で限定し、`sts:ExternalId` 条件を必須にしたロールを作る。

## Signature

```hcl
module "x" { source = "./modules/iam-cross-account-trust", name, trusted_principal_arns, external_id, require_mfa = false,
             policy_arns = [], max_session_duration = 3600, tags = {} }
-> { role_arn, role_name, requires_external_id }
```

## Usage

```hcl
module "auditor_trust" {
  source                 = "./modules/iam-cross-account-trust"
  name                   = "example-auditor"
  trusted_principal_arns = ["arn:aws:iam::210987654321:role/auditor"]
  external_id            = var.auditor_external_id # 相手と共有する秘密
  policy_arns            = [module.logs_read_only.policy_arn]
}
# 引き受け側: aws sts assume-role --role-arn <role_arn> --external-id <external_id>
```

## Contract

- 信頼ポリシーは `Principal.AWS = trusted_principal_arns` からの `sts:AssumeRole` 1 文だけ。`Condition.StringEquals["sts:ExternalId"]` が必ず付き、`requires_external_id` 出力は常に `true`
- `require_mfa = true` で `Bool["aws:MultiFactorAuthPresent"] = "true"` が加わる（既定 `false` では付かない）。MFA を付けても ExternalId 条件は残る
- 弾く入力: 空や `*` の `external_id`（2〜1224 文字の `A-Za-z0-9+=,.@:/_-` のみ）、`*` や素のアカウント ID や 12 桁でない ID を含む `trusted_principal_arns`（`arn:aws:iam::<12 桁>:root` / `role/…` / `user/…` のみ）、3600〜43200 秒外のセッション時間
- `external_id` は `sensitive`。plan の出力には表示されない
- `policy_arns` は `for_each` で attach。既定は `[]`（引き受けても何もできない）
- `tags` はロールに付く。`max_session_duration` の既定は 3600
- 冪等。`external_id` の変更は信頼ポリシーの更新だけで再作成しない

## Alternatives

- 同じ Organization 内で多数のアカウントに同じ権限を配るなら、Organizations の SCP + `aws:PrincipalOrgID` 条件、または IAM Identity Center の permission set。ExternalId は主に第三者（SaaS）向け
- 引き受け元が人ではなく CI / ワークロードなら `iam-service-identity`（OIDC）。アカウント間でもロールチェーンは避けられる
- リソース単位の共有（バケットだけ、キューだけ）なら相手アカウントをリソースポリシーで許可する方がロールより小さい

## Pitfalls

- ExternalId は「秘密」ではなく「混乱した代理（confused deputy）」対策。相手 SaaS が生成した値をそのまま使い、利用側ごとに変える。漏れても principal 制限があるので即侵害にはならない
- `:root` を信頼すると、相手アカウントの IAM 管理者が任意のユーザー / ロールに引き受けを許可できる。相手側の統制を信じられないなら `role/…` で絞る
- 引き受け側のロール ARN を信頼して相手がそのロールを消して作り直すと、信頼ポリシー内の ARN は一意 ID に解決されているため `Principal` が壊れる（表示は ARN ではなく `AROA…`）。再 apply が要る
- GCP のクロスプロジェクトは principal を直接 IAM binding に書く方式で、ExternalId に相当する仕組みが無い。Azure は別テナントに対して Lighthouse / ゲストユーザーになる
- `max_session_duration` を伸ばしても、引き受け元がすでにロールセッションだと 1 時間で切れる

## Test

`modules/iam-cross-account-trust/tests/iam-cross-account-trust.tftest.hcl`
