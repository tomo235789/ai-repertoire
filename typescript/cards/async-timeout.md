---
id: async-timeout
lang: typescript
title: Promise に制限時間を設ける
tags: [タイムアウト, 制限時間, 打ち切り, 時間切れ, timeout, deadline, time-limit]
lib: es-toolkit
fn: withTimeout
since: "1.48.0"
verified: 2026-09-17
status: public
---

非同期処理が `ms` 以内に終わらなければ `TimeoutError` で reject する。外部 API 呼び出しの待ちすぎ防止に使う。

## Signature

```ts
function withTimeout<T>(run: () => Promise<T>, ms: number, { signal }?: WithTimeoutOptions): Promise<T>
```

## Usage

```ts
import { TimeoutError, withTimeout } from 'es-toolkit';

try {
  const data = await withTimeout(() => fetchJson('/api/items'), 3_000);
  // => 3 秒以内に終われば fetchJson の結果
} catch (err) {
  if (err instanceof TimeoutError) console.log('3 秒以内に終わらなかった');
  else throw err;
}
```

## Contract

- `run` は `withTimeout` の呼び出し時に同期的に 1 回だけ呼ばれる。`ms` 以内に resolve すればその値で resolve する
- `ms` 経過までに `run()` が決着しなければ `TimeoutError`（es-toolkit が export するクラス、`DOMException` のサブクラス）で reject する
- タイムアウトしても `run()` が返した元の `Promise` は止まらない。処理は裏で最後まで走り、結果は捨てられる
- `run()` が reject した場合はそのエラーがそのまま伝わる
- `signal` が abort されるとタイムアウト側のタイマーだけが止まり、`run()` の決着を待つ。呼び出し時点で既に abort 済みならタイムアウトは働かない
- `run()` が先に決着してもタイムアウト用の `setTimeout` は残る（`ms` 経過時に何もせず消える）

## Alternatives

- 処理そのものを中断したい（`fetch` など `AbortSignal` を受け取れるもの）なら `AbortSignal.timeout(ms)` を渡す方が確実。`withTimeout` は待つのをやめるだけ
- 制限時間だけを表す `Promise` が欲しいなら `timeout(ms)`（es-toolkit。`ms` 後に `TimeoutError` で reject する）
- 依存を増やせない場合は `Promise.race([run(), new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms))])`

## Pitfalls

- `TimeoutError` の `name` は `'Error'`（`DOMException` の既定名）。`AbortSignal.timeout()` が投げる `DOMException`（`name` が `'TimeoutError'`）とは別物なので、判定は `instanceof TimeoutError` で行う
- 元の処理はキャンセルされないので、副作用のある処理（書き込み・送金など）に付けると「タイムアウトしたのに完了している」状態が起こり得る
- `run` には `Promise` ではなく **`Promise` を返す関数** を渡す。`withTimeout(fetchJson(...), ms)` は型エラー

## Test

`examples/async-timeout.test.ts`
