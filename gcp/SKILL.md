---
name: gcp-repertoire
description: Google Cloud の設定（Cloud Storage / IAM / VPC / Cloud Run / Secret Manager / Pub/Sub / Cloud SQL / Cloud Logging / Cloud CDN）を SDK やテンプレートに渡す前に読む。ベストプラクティスを「要求 → 設定」の純粋関数として提供し、公開アクセス禁止・暗号化・最小権限を既定にする
---

# gcp-repertoire

Google Cloud のリソース設定を組み立てたくなったら、実装する前にこの Skill の手順に従う。

## 返り値の形

GCP は API の種類でキーの書き方が変わるので、カードごとに揃えてある。

- Discovery ベースの API（Compute / Cloud SQL / IAM / Cloud Storage）は REST のワイヤ形式なので camelCase。`googleapiclient` の `body=` にそのまま渡す
- クライアントライブラリ（Cloud Run / Cloud Functions / Pub/Sub / KMS / Logging / Monitoring）は protobuf のフィールド名なので snake_case
- どちらを返すかは各カードの `## Usage` が示す呼び出しで決まる。混ぜると値が落ちる

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語で検索する
2. 該当カードがあれば `examples/<id>.py` の純粋関数を使う。入力は業務語の要求、出力は SDK やテンプレートにそのまま渡せる dict。`## Contract` が出力の保証（許可する操作の一覧・暗号化・公開禁止・ラベル）
3. 該当がなければ自前で書いてよい。ただし同じ形式のカードを `status: public` で提案する（PR テンプレートの抽象化チェックリストを通す）

## 前提

- 関数は **副作用を持たない**（API 呼び出し・認証・環境変数の参照はしない）。呼び出し側が SDK に渡す
- テストは `examples/<id>_test.py`（pytest。出力の構造と Contract の各項目をアサートする。クラウドには接続しない）
- プロジェクト ID / サブスクリプション ID / リソース ID などの実値は関数の引数で受け取り、カードの例には合成値だけを使う
- `lib` は gcp.storage / gcp.iam / gcp.compute / gcp.run / gcp.secretmanager / gcp.pubsub / gcp.sql / gcp.logging / gcp.monitoring のようにサービス単位で書く

## カード一覧

`cards/` 配下。ファイル名 = カード ID。同じ ID を `aws/` と `terraform/` でも使っている（`reference/index.md` がクラウド横断の対応表になる）。
