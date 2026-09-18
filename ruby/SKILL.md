---
name: ruby-repertoire
description: Ruby で配列・ハッシュ・文字列・日付のユーティリティを書く前に読む。自前のループを書かず Enumerable / Hash / Comparable / Date / Time の既存メソッドへ誘導する
---

# ruby-repertoire

Ruby（3.4 以上）で「ちょっとしたユーティリティ」を書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature` と `## Contract` に従って既存メソッドを使う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: public` で `cards/` に提案する（PR テンプレートの抽象化チェックリストを通す）

## 参照先

stdlib のみ（`Enumerable`、`Array`、`Hash`、`Comparable`、`Float`、`String`、`Date` / `Time`、`Timeout`）。ActiveSupport は使わない。

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。テストは `examples/<id>_test.rb`（minitest、`ruby/run_tests.sh` で実行）。
