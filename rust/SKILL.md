---
name: rust-repertoire
description: Rust でイテレータ・スライス・マップ・文字列・日時のユーティリティを書く前に読む。自前のループを書かず std（Iterator / slice / OnceLock）と itertools / chrono の既存 API へ誘導する
---

# rust-repertoire

Rust（stable）で「ちょっとしたユーティリティ」を書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature` と `## Contract` に従って既存 API を使う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: public` で `cards/` に提案する（PR テンプレートの抽象化チェックリストを通す）

## 参照先

| 領域 | 既定 |
|---|---|
| collection | `Iterator` / `slice` のメソッド（chunks / windows / partition / zip / flatten / sort_by_key）。キー付き操作は `itertools` |
| number / string | `Ord::clamp` / `f64::clamp`、`f64::round`、`format!` の幅指定 |
| date | `chrono`（`DateTime::to_rfc3339`、`Duration::days`） |
| function | `std::sync::OnceLock` / `LazyLock` |

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。テストは `tests/<id をアンダースコアに置換>.rs`（`cargo test`）。
