---
name: aws-repertoire
description: AWS の設定（S3 / IAM / VPC / Lambda / ECS / Secrets Manager / SQS / SNS / RDS / CloudWatch / CloudFront）を SDK や CloudFormation に渡す前に読む。ベストプラクティスを「要求 → 設定」の純粋関数として提供し、公開アクセス禁止・暗号化・最小権限を既定にする
---

# aws-repertoire

AWS リソースの設定を組み立てたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語で検索する
2. 該当カードがあれば、`examples/<id>.py` の純粋関数を使う。入力は業務語の要求（dataclass）、出力は boto3 の API や CloudFormation にそのまま渡せる dict。`## Contract` が出力の保証（許可 action の一覧・暗号化・公開禁止・タグ）
3. 該当がなければ自前で書いてよい。ただし同じ形式のカードを `status: public` で提案する（PR テンプレートの抽象化チェックリストを通す）

## 前提

- 関数は **副作用を持たない**（API 呼び出し・認証・環境変数の参照はしない）。呼び出し側が boto3 に渡す
- テストは `examples/<id>_test.py`（pytest。出力の構造と Contract の各項目をアサートする。AWS には接続しない）
- アカウント ID / ARN / リージョンなどの実値は関数の引数で受け取り、カードの例には合成値（`123456789012`、`us-east-1`）だけを使う

## カード一覧

`cards/` 配下。ファイル名 = カード ID。同じ ID を `terraform/` と `gcp/` `azure/` で揃える。
