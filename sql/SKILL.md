---
name: sql-repertoire
description: SQL で重複除去・グループ集計・窓関数・日付演算・丸めなどを書く前に読む。アプリ側のループや自前の集計に逃げず、方言ごとの正しい構文へ誘導する
---

# sql-repertoire

SQL で「この集計はどう書くのが正しいか」に迷ったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature`（構文の形）と `## Contract`（NULL・順序・型の扱い）に従う。`## Usage` はカードの `lib` の方言で書かれている。他方言は `## Alternatives`
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: public` で `cards/` に提案する（PR テンプレートの抽象化チェックリストを通す）

## 前提

- `lib` は方言名（`sqlite` / `duckdb`）。`fn` は構文または関数名。PostgreSQL / MySQL / BigQuery の書き方は各カードの Alternatives に書く
- テストは `examples/<id>_test.py`（pytest）。同じクエリを sqlite と duckdb で実行して結果を確認する（方言固有の構文は片方だけ）

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。
