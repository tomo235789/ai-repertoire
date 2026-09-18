---
id: http-rate-limit-backoff
lang: typescript
title: レート制限に指数バックオフで対処する
tags: [レート制限, 指数バックオフ, 待って再試行, スロットリング, rate-limit, backoff, retry-after, "429"]
lib: es-toolkit
fn: retry
since: "1.51.0"
verified: 2026-09-17
status: public
---

429 / 503 を受けたら `Retry-After` ヘッダーの秒数、無ければ指数バックオフ + ジッターだけ待ってやり直す。API の呼び出し制限に当たったときに使う。

## Signature

```ts
function retry<T>(func: () => Promise<T>, options: RetryOptions): Promise<T>
// delay: (attempts: number, error: unknown) => number  — attempts は 0 始まり、error はその試行で投げた値
```

## Usage

```ts
import { retry } from 'es-toolkit';

class RateLimited extends Error { constructor(public status: number, public retryAfterMs: number | null) { super(`HTTP ${status}`); } }
const res = await retry(async () => {
  const res = await fetch('https://example.com/items', { signal });
  if (res.status === 429 || res.status === 503) throw new RateLimited(res.status, Number(res.headers.get('retry-after')) * 1000 || null);
  return res;
}, { retries: 5, shouldRetry: (e) => e instanceof RateLimited,
     delay: (attempt, e) => (e as RateLimited).retryAfterMs ?? Math.min(500 * 2 ** attempt, 30_000) + Math.random() * 500 });
// => 待ち時間: Retry-After 秒 × 1000、無ければ 500, 1000, 2000, 4000, 8000ms（上限 30 秒）+ 0〜500ms
```

## Contract

- `delay(attempts, error)` は失敗のたびに呼ばれ、返したミリ秒だけ待ってから次の試行に入る。`attempts` は 0 始まりなので `base * 2 ** attempts` の 1 回目は `base`
- `error` にはその試行で投げた値がそのまま渡る。`Response` から読んだ `Retry-After` をエラーに載せておけば `delay` で参照できる
- `Retry-After` は秒数（`"3"`）か HTTP 日付（`"Wed, 21 Oct 2015 07:28:00 GMT"`）。`Number()` は日付のとき `NaN` になるので `Date.parse(v) - Date.now()` にフォールバックする。`headers.get` は大文字小文字を区別しない
- `shouldRetry` で 429 と 503 に限定する。それ以外の 5xx やネットワーク断はカード http-retry-idempotent の判定と組み合わせる
- `retries` 回すべて失敗したら最後のエラーを投げる。最後の試行のあとは待たない
- `Math.min(..., cap)` で上限を付けないと `2 ** attempts` は数回で分単位になる

## Alternatives

- 制限に当たる前に送信間隔を制御するなら `p-throttle` や `bottleneck`（トークンバケット）
- 複数リクエストを並列に送るなら `Semaphore`（カード async-limit-concurrency）で同時数を絞る方が先
- 「フルジッター」（`Math.random() * min(cap, base * 2 ** attempt)`）は同時に多数のクライアントが再試行するときの衝突をさらに減らす

## Pitfalls

- `Retry-After` が返っているのに指数バックオフで短く待つと、サーバーの指示より早く叩いて再度 429 になる。ヘッダーを優先する
- ジッターなしだと、同じタイミングで失敗した全クライアントが同じ時刻に再試行して再び制限に当たる
- 429 は「このクライアントの送りすぎ」、503 は「サーバー側の過負荷」で、どちらも再試行の間隔を **増やす** 方向にしか対処できない。総待ち時間の上限（`retries` と `cap`）を決めておく
- `delay` が `Math.random()` を含むとテストが不安定になる。`vi.spyOn(Math, 'random')` で固定するか、ジッターを注入できる引数にする
- 待機は `setTimeout` なので `signal` を abort しても止まらない。長い待機を即座に打ち切りたいなら `delay` を短く刻む

## Test

`examples/http-rate-limit-backoff.test.ts`
