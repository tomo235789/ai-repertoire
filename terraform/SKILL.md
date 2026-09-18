---
name: terraform-repertoire
description: Terraform で AWS のバケット・IAM・ネットワーク・コンピュート・シークレット・キュー・DB・監視を書く前に読む。ベストプラクティスを「要求 → 設定」の純粋な module として提供し、公開アクセス禁止・暗号化・最小権限・タグを既定にする
---

# terraform-repertoire

Terraform で AWS リソースを書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語で検索する（例: 「非公開バケット」「最小権限」「プライベートサブネット」）
2. 該当カードがあれば、`modules/<id>/` をそのまま `module` ブロックで呼ぶ。`## Contract` が出力の保証（公開禁止・暗号化・タグ・冪等性）で、`## Signature` が variables → outputs
3. 該当がなければ自前で書いてよい。ただし同じ形式のカードと module を `status: public` で提案する（PR テンプレートの抽象化チェックリストを通す）

## 前提

- module は **provider ブロックを持たない純粋関数**（variables → outputs）。provider と backend は呼び出し側が持つ
- テストは `modules/<id>/tests/<id>.tftest.hcl`（`mock_provider "aws" {}` + `command = plan`。資格情報なしで CI が実行する）
- `terraform/run_tests.sh` が各 module で `terraform init -backend=false` → `validate` → `tflint` → `terraform test` を実行する

## カード一覧

`cards/` 配下。ファイル名 = カード ID。同じ ID を `aws/`（SDK 向けの純粋関数）と `gcp/` `azure/` で揃える。
