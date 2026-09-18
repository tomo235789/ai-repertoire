---
id: http-pagination-cursor
lang: typescript
title: カーソル式ページネーションを最後まで読む
tags: [ページネーション, カーソル, 全件取得, 逐次取得, pagination, cursor, async-generator, for-await]
lib: stdlib
fn: async generator
since: "ES2018"
verified: 2026-09-17
status: public
---

`nextCursor` を返す API を `async function*` で包み、無くなるまでページを取りに行きながら要素を 1 つずつ `yield` する。呼び出し側は `for await` で受け取り、途中で止められる。

## Signature

```ts
async function* paginate<T>(fetchPage: (cursor?: string) => Promise<{ items: T[]; nextCursor?: string }>): AsyncGenerator<T>
```

## Usage

```ts
async function* paginate<T>(fetchPage: (cursor?: string) => Promise<{ items: T[]; nextCursor?: string }>) {
  let cursor: string | undefined;
  do {
    const page = await fetchPage(cursor);
    yield* page.items;
    cursor = page.nextCursor;
  } while (cursor !== undefined);
}  // cursor は不透明トークン。searchParams でエンコードする（+ や & を含んでも壊れない）
const fetchPage = async (c?: string) => (await fetch(`https://example.com/items?${new URLSearchParams(c ? { cursor: c } : {})}`)).json();
for await (const item of paginate<{ id: number }>(fetchPage)) if (item.id > 100) break; // 途中で止められる
```

## Contract

- 1 ページ目は `fetchPage(undefined)` で取り、返ってきた `items` を順に `yield` してから `nextCursor` で次を取る。`nextCursor` が `undefined` になったページで終わる
- 遅延評価。`paginate(fetchPage)` を呼んだだけでは `fetchPage` は呼ばれず、最初の `next()`（`for await` の 1 周目）で 1 ページ目を取る。次のページは前のページの要素を **すべて消費したあと** に取る
- `for await` を `break` / `return` / `throw` で抜けると generator の `return()` が呼ばれて終了し、それ以降のページは取らない。generator 内の `finally` も実行される
- `fetchPage` が reject したらそのエラーが `for await` の位置で throw される
- `items` が空で `nextCursor` があるページは何も `yield` せずに次へ進む
- 全件を配列にするなら `await Array.fromAsync(paginate(fetchPage))`（Node 22 以降）

## Alternatives

- ページ単位で扱いたい（件数表示・並列処理）なら `yield page`（`AsyncGenerator<Page<T>>`）にして呼び出し側で `items` を回す
- オフセット式（`?page=2` / `?offset=100`）でも同じ形で、`cursor` の代わりにページ番号を進める。総件数が変わると重複・欠落が起こる点だけ異なる
- `Link` ヘッダー（`rel="next"`）で次を示す API なら `res.headers.get('link')` を解析して URL を `cursor` にする

## Pitfalls

- 次のページを取るのは前のページを消費し切ったあとなので、1 件ごとの処理が遅いと全体も遅い。先読みしたいなら `fetchPage` 側でページを 1 つ先に取り始める
- `nextCursor` が `null` で返る API では `cursor !== undefined` が真のままになり **無限ループ** する。`page.nextCursor ?? undefined` で正規化する
- `break` しても既に取得済みの `Response` 本文は読み終わっている。`fetchPage` の中で `fetch` を中断したいなら `AbortSignal` を渡す
- generator を 2 回回すことはできない。`const g = paginate(...)` を使い切ったら作り直す
- `Array.fromAsync` は全件をメモリに載せる。件数の上限が分からない API では `for await` で逐次処理する

## Test

`examples/http-pagination-cursor.test.ts`
