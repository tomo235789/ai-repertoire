---
name: cpp-repertoire
description: C++ でコンテナ・範囲・文字列・時刻・並行処理のユーティリティを書く前に読む。生のループを書かず std::ranges / <algorithm> / <chrono> / <format> の既存機能へ誘導する
---

# cpp-repertoire

C++（C++20 / 23、GCC 14 以降。`std::ranges::to` を使うため）で「ちょっとしたユーティリティ」を書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
2. 該当カードがあれば、その `## Signature` と `## Contract` に従って既存機能を使う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: draft` で `cards/` に提案する（`../schema/card.schema.json` と `../README.md` の「カードの書き方」を参照）

## 参照先

| 領域 | 既定 |
|---|---|
| collection | `std::ranges` のアルゴリズムと `std::views`（chunk / slide / zip / join / take_while / chunk_by）、`fold_left`（C++23） |
| number / string | `std::clamp`、`<cmath>`、`std::format` |
| date | `<chrono>`（`sys_days`、`std::format("{:%F}")`） |
| function / async | `std::call_once`、`std::counting_semaphore`、`std::future::wait_for` |

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。テストは `examples/<id>_test.cpp`（`cpp/run_tests.sh` で実行）。
