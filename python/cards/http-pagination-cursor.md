---
id: http-pagination-cursor
lang: python
title: カーソル式ページネーションを最後まで読む
tags: [ページネーション, カーソル, 全件取得, 逐次取得, pagination, cursor, generator, yield-from]
lib: stdlib
fn: generator
since: "3.0"
verified: 2026-09-17
status: public
---

`next_cursor` を返す API をジェネレータ関数で包み、無くなるまでページを取りに行きながら要素を 1 つずつ `yield` する。呼び出し側は `for` で受け取り、途中で止められる。

## Signature

```python
def paginate(fetch_page: Callable[[str | None], dict[str, Any]]) -> Iterator[Any]
```

## Usage

```python
def paginate(fetch_page):
    cursor = None
    while True:
        page = fetch_page(cursor)          # 1 ページ目は None で呼ぶ
        yield from page["items"]
        cursor = page.get("next_cursor")
        if not cursor:                     # None / "" / キー無しで終了
            break
fetch_page = lambda cursor: httpx.get("https://example.com/items", params={"cursor": cursor or ""}).json()
for item in paginate(fetch_page): ...  # 遅延取得。break で止めれば以降のページは取らない
```

## Contract

- 1 ページ目は `fetch_page(None)` で取り、返ってきた `items` を順に `yield` してから `next_cursor` で次を取る。`next_cursor` が **偽値**（`None` / `""` / キー無し）のページで終わる
- 遅延評価。`paginate(fetch_page)` を呼んだだけでは `fetch_page` は呼ばれず、最初の `next()`（`for` の 1 周目）で 1 ページ目を取る。次のページは前のページの要素を **すべて消費したあと** に取る
- `for` を `break` で抜けるとジェネレータは以降のページを取らない。参照が消えた時点（または `close()`）で `GeneratorExit` が中で起き、`finally` があれば実行される
- `fetch_page` が例外を投げたらそのまま `for` の位置で投げ直され、ジェネレータは終了する
- `items` が空で `next_cursor` があるページは何も `yield` せずに次へ進む
- 使い切ったジェネレータをもう一度回しても何も出ない。全件を `list(paginate(fetch_page))` にするときは 1 回だけ

## Alternatives

- ページ単位で扱いたい（件数表示・並列処理）なら `yield page` にして呼び出し側で `items` を回す
- `async def fetch_page` なら `async def paginate` にして `for item in page["items"]: yield item`（`yield from` は `async def` で使えない）。呼び出しは `async for`
- `Link` ヘッダー（`rel="next"`）で次を示す API なら `response.links.get("next", {}).get("url")` を `cursor` にする
- オフセット式（`?page=2` / `?offset=100`）も同じ形で、`cursor` の代わりにページ番号を進める。総件数が変わると重複・欠落が起こる点だけ異なる

## Pitfalls

- TypeScript 版は `cursor !== undefined` で判定するので `null` が返ると無限ループするが、Python の `if not cursor` は `None` / `""` / `0` をすべて終了として扱う。逆に **`0` や `"0"` が正当なカーソル** の API では `if cursor is None` に変える
- 次のページを取るのは前のページを消費し切ったあとなので、1 件ごとの処理が遅いと全体も遅い。先読みしたいなら `fetch_page` 側で非同期に取り始める
- `next_cursor` が前のページと同じ値を返し続ける API（バグやレート制限時のエラー応答）だと止まらない。ページ数の上限や「同じカーソルなら終了」の判定を足す
- `list(...)` は全件をメモリに載せる。件数の上限が分からない API では `for` で逐次処理する
- ジェネレータを 2 回回すことはできない。`g = paginate(...)` を使い切ったら作り直す

## Test

`examples/http-pagination-cursor_test.py`
