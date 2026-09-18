---
id: error-aggregate
lang: typescript
title: 複数のエラーを 1 つにまとめる
tags: [複数エラー, エラーの集約, まとめて報告, 並列失敗, AggregateError, errors, Promise.any, multiple-errors]
lib: stdlib
fn: AggregateError
since: "ES2021"
verified: 2026-09-17
status: public
---

複数のエラーを `errors` 配列に持つ 1 つの `Error` として投げる。並列処理の失敗をまとめて報告したり、`Promise.any` の全滅を扱うのに使う。

## Signature

```ts
new AggregateError(errors: Iterable<unknown>, message?: string, options?: { cause?: unknown }): AggregateError
// err.errors: unknown[]  — 渡した iterable を配列にしたもの
```

## Usage

```ts
const results = await Promise.allSettled(urls.map((u) => fetch(u)));
const failures = results.filter((r): r is PromiseRejectedResult => r.status === 'rejected').map((r) => r.reason);
if (failures.length > 0) throw new AggregateError(failures, `${failures.length} 件の取得に失敗`);
// catch 側:
// if (err instanceof AggregateError) for (const e of err.errors) console.error(e);

await Promise.any([Promise.reject(new Error('a')), Promise.reject(new Error('b'))]);
// => AggregateError: All promises were rejected（errors は [Error: a, Error: b]）
```

## Contract

- 第 1 引数は任意の iterable。`errors` プロパティには **配列に変換した新しいコピー** が入り、要素は `Error` でなくてもよい（文字列などもそのまま）
- `message` を省略すると `''`。`name` は `'AggregateError'`、`instanceof Error` も `true`。`options.cause` も他の `Error` と同じく使える
- `errors` は列挙されないプロパティ。`JSON.stringify` には現れず、`util.inspect` では `[errors]: [...]` として表示される
- `Promise.any` はすべて reject したとき `AggregateError` で reject し、`errors` は入力と同じ順序（message は実装依存なので判定に使わない）。空配列を渡しても `AggregateError` で `errors` は `[]`
- `Promise.allSettled` は reject しないので、失敗をまとめるには自分で `AggregateError` を作る
- `errors` の中に `AggregateError` を入れて入れ子にもできる

## Alternatives

- 最初の失敗で即座に知りたいなら `Promise.all`（最初の reject がそのまま伝わる。ただし開始済みの処理は止まらず、結果が無視されるだけ）
- 1 つの原因だけ包むならカード error-cause-chain（`cause`）
- 検証エラーの一覧のように「エラーではない値の配列」で足りるなら `Result` の配列（`neverthrow` の `Result.combineWithAllErrors`）

## Pitfalls

- `err.message` だけログに出すと個々の原因が見えない。必ず `err.errors` を展開する（カード log-structured の展開関数で `errors` も扱う）
- `Promise.any` の `AggregateError` は要素が多いと `errors` が大きい。件数と先頭数件だけ報告する
- `errors` は `unknown[]`。要素を使うときは `instanceof Error` で絞る
- `Promise.any([])` は同期的にでなく reject で `AggregateError` を返す。「候補ゼロ」を事前に弾く
- TypeScript の `lib` に `ES2021` 以上が無いと `AggregateError` の型が無い（実行時は Node 15+ で動く）

## Test

`examples/error-aggregate.test.ts`
