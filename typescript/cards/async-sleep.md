---
id: async-sleep
lang: typescript
title: 指定ミリ秒待つ
tags: [待機, スリープ, 遅延, 一時停止, sleep, delay, wait]
lib: es-toolkit
fn: delay
since: "1.4.0"
verified: 2026-09-17
status: public
---

指定ミリ秒後に resolve する `Promise` を返す。ポーリング間隔やリトライ前の待機、テストのタイミング調整に使う。

## Signature

```ts
function delay(ms: number, { signal }?: DelayOptions): Promise<void>
```

## Usage

```ts
import { AbortError, delay } from 'es-toolkit';

await delay(500); // 500ms 待つ
const controller = new AbortController();
const waiting = delay(10_000, { signal: controller.signal });
controller.abort();
await waiting.catch((e) => console.log(e instanceof AbortError));
// => true（AbortError で reject される）
```

## Contract

- `ms` ミリ秒後に `undefined` で resolve する。値は返さない
- `signal` が abort されると内部の `setTimeout` を止め、`AbortError`（es-toolkit が export するクラス）で reject する。呼び出し時点で既に abort 済みなら即座に reject する
- 負の `ms` は例外にならず、`setTimeout` の仕様どおり最短で resolve する

## Alternatives

- 依存を増やせない場合は `new Promise((r) => setTimeout(r, ms))`
- Node.js なら `node:timers/promises` の `setTimeout(ms, undefined, { signal })` が同じ役割（abort 時は `AbortError` という `name` の `Error`）
- 別の非同期処理に制限時間を付けたいなら `withTimeout`（カード async-timeout）

## Pitfalls

- `AbortError` の `name` は `'Error'`（`DOMException` の既定名）。`err.name === 'AbortError'` では判定できないので `err instanceof AbortError` を使う
- 引数は秒ではなくミリ秒
- テストでは `vi.useFakeTimers()` と `vi.advanceTimersByTimeAsync(ms)` で進める。実時間で待つと遅く不安定になる

## Test

`examples/async-sleep.test.ts`
