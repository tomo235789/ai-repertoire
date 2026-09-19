---
name: azure-repertoire
description: Azure の設定（Storage / Entra ID・RBAC / VNet / Container Apps / Key Vault / Service Bus / SQL Database / Monitor / Front Door）を SDK やテンプレートに渡す前に読む。ベストプラクティスを「要求 → 設定」の純粋関数として提供し、公開アクセス禁止・暗号化・最小権限を既定にする
---

# azure-repertoire

Azure のリソース設定を組み立てたくなったら、実装する前にこの Skill の手順に従う。

## 返り値の形

関数は「SDK の呼び出し引数」と「ARM に送る body」を分けて返す。

- 呼び出し引数にあたるトップレベルのキー（`account` / `container` / `role_assignment` / `usable_addresses` など）は Python 側の名前なので snake_case
- その中の body（`properties` の下や `parameters` の中）は **ARM のワイヤ形式** なので camelCase

この 2 つを混ぜると `azure-mgmt-*` のシリアライザが値を落とす。`properties` でくるんだ dict の中は必ず camelCase にする。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語で検索する
2. 該当カードがあれば `examples/<id>.py` の純粋関数を使う。入力は業務語の要求、出力は SDK やテンプレートにそのまま渡せる dict。`## Contract` が出力の保証（許可する操作の一覧・暗号化・公開禁止・ラベル）
3. 該当がなければ自前で書いてよい。ただし同じ形式のカードを `status: public` で提案する（PR テンプレートの抽象化チェックリストを通す）

## 前提

- 関数は **副作用を持たない**（API 呼び出し・認証・環境変数の参照はしない）。呼び出し側が SDK に渡す
- テストは `examples/<id>_test.py`（pytest。出力の構造と Contract の各項目をアサートする。クラウドには接続しない）
- プロジェクト ID / サブスクリプション ID / リソース ID などの実値は関数の引数で受け取り、カードの例には合成値だけを使う
- `lib` は azure.storage / azure.authorization / azure.network / azure.containerapps / azure.keyvault / azure.servicebus / azure.sql / azure.monitor / azure.cdn のようにサービス単位で書く

## カード一覧

`cards/` 配下。ファイル名 = カード ID。同じ ID を `aws/` と `terraform/` でも使っている（`reference/index.md` がクラウド横断の対応表になる）。
