---
name: go-repertoire
description: Go でスライス・マップ・文字列・時刻・並行処理のユーティリティを書く前に読む。自前のループを書かず slices / maps / time / sync と samber/lo の既存関数へ誘導する
---

# go-repertoire

Go で「ちょっとしたユーティリティ」を書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature` と `## Contract` に従って既存関数を使う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: draft` で `cards/` に提案する（`../schema/card.schema.json` と `../README.md` の「カードの書き方」を参照）

## 参照先ライブラリ

| 領域 | 既定 |
|---|---|
| collection / object | stdlib の `slices` / `maps`（Go 1.21+）。キー関数付きの操作は `github.com/samber/lo` |
| number / string | stdlib（`math`、`strings`、組み込み `min` / `max`）。ケース変換・切り詰めは `samber/lo` |
| date | stdlib `time`（`AddDate`、`time.Date`、`RFC3339`） |
| function / async | stdlib `sync`（`OnceValue`）、`context`、`golang.org/x/sync/errgroup` |

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。機能別の言語横断リファレンスは生成物 `reference/<id>.md` にある。
