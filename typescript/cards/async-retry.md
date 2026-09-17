---
id: async-retry
lang: typescript
title: 失敗した非同期処理を再試行する
tags: [再試行, リトライ, 失敗時の再実行, バックオフ, retry, backoff, resilience]
lib: es-toolkit
fn: retry
since: "1.51.0"
verified: 2026-09-17
status: public
---

`Promise` を返す関数が reject したら待って再実行し、成功した値を返す。一時的なネットワークエラーへの対処に使う。

## Signature

```ts
function retry<T>(func: () => Promise<T>): Promise<T>
function retry<T>(func: () => Promise<T>, retries: number): Promise<T>
function retry<T>(func: () => Promise<T>, options: RetryOptions): Promise<T>
```

## Usage

```ts
import { retry } from 'es-toolkit';

const data = await retry(() => fetchJson('/api/items'), {
  retries: 3,                                  // 最大 3 回やり直す（合計 4 回まで）
  delay: (attempt) => 100 * 2 ** attempt,      // 100, 200, 400ms の指数バックオフ
  shouldRetry: (err) => !(err instanceof TypeError),
});
// => 成功した回の値。4 回とも失敗したら最後のエラーで reject
```

## Contract

- `func` を呼び、reject したら `delay` だけ待って再実行する。resolve した時点でその値を返す
- `retries` は **再試行の回数**。合計で最大 `retries + 1` 回呼ぶ。省略時は `Infinity`（成功するまで無限に試す）。第 2 引数に数値を渡すと `retries` として扱う
- `delay` は数値（ミリ秒）か `(attempts, error) => number`。`attempts` は失敗した試行の 0 始まりの番号、`error` はその試行のエラー。省略時は `0`
- すべて失敗したら **最後の試行のエラー** をそのまま投げる。最後の試行のあとには待たない
- `shouldRetry(error, attempt)` が `false` を返すと即座にそのエラーを投げる
- `signal` は各試行の直前に確認する。開始時点で abort 済みなら `func` を呼ばずに `Error` を投げる。途中で abort されたら、進行中の待機が終わったあと直前のエラーを投げる（待機自体は中断されない）

## Alternatives

- 1 回ごとに制限時間も付けたいなら `withTimeout`（カード async-timeout）を `func` の中で組み合わせる
- ジッターや `Retry-After` ヘッダー対応など細かい制御が要るなら `p-retry` / `async-retry`
- 依存を増やせない場合は `for` ループと `try/catch` と `delay`

## Pitfalls

- `retries` を省略すると無限に再試行する。必ず上限を付けるか `shouldRetry` で打ち切る
- abort しても待機中の `delay` は止まらない。長いバックオフを `AbortSignal` で即座に止めたいなら `delay` を短く刻むか自前で `delay(ms, { signal })` を使う
- `delay` コールバックの `attempts` は 0 始まり。`2 ** attempts` で指数バックオフにすると 1 回目の待機は `1 倍`
- 冪等でない処理（送金・投稿）を再試行すると二重実行になる。`shouldRetry` で送信前のエラーだけに限定する

## Test

`examples/async-retry.test.ts`
