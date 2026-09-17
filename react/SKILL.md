---
name: react-repertoire
description: React でコンポーネントやフックを書く前に読む。派生状態・副作用の後始末・データ取得・フォーム・コンテキストなど、再発明しがちなパターンを既知の形へ誘導する
---

# react-repertoire

React で「この処理はどう書くのが正しいか」に迷ったら、実装する前にこの Skill の手順に従う。純粋関数ではなくパターン粒度のカードで、ID は `pattern-*`。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature`（コンポーネント / フックの形）と `## Contract`（レンダーと副作用の保証）に従う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: public` で `cards/` に提案する（PR テンプレートの抽象化チェックリストを通す。`../schema/card.schema.json` と `../README.md` の「カードの書き方」を参照）

## 前提

- React 19、関数コンポーネントとフックのみ。クラスコンポーネントは Error Boundary だけ
- テストは vitest + Testing Library（`examples/`）。ユーザー操作は `@testing-library/user-event`

## カード一覧

`cards/` 配下。ファイル名 = カード ID。機能別のリファレンスは生成物 `reference/<id>.md` にある。
