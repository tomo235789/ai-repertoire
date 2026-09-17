---
name: csharp-repertoire
description: C# でコレクション・辞書・文字列・日時・非同期のユーティリティを書く前に読む。自前のループを書かず LINQ / System 名前空間と MoreLINQ / Polly の既存 API へ誘導する
---

# csharp-repertoire

C# で「ちょっとしたユーティリティ」を書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature` と `## Contract` に従って既存 API を使う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: public` で `cards/` に提案する（PR テンプレートの抽象化チェックリストを通す。`../schema/card.schema.json` と `../README.md` の「カードの書き方」を参照）

## 参照先ライブラリ

| 領域 | 既定 |
|---|---|
| collection / object | `System.Linq`（.NET 6+ の `Chunk` / `DistinctBy` など）。窓・分割など足りないものは MoreLINQ |
| number / string | `System.Math`、`string` のメソッド |
| date | `DateTime` / `DateTimeOffset`（ISO 8601 は `"o"` 書式） |
| function / async | `Lazy<T>`、`ConcurrentDictionary`、`Task.Delay` / `WaitAsync`、`SemaphoreSlim`。リトライは Polly |

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。機能別の言語横断リファレンスは生成物 `reference/<id>.md` にある。
