---
id: http-retry-idempotent
lang: typescript
title: 冪等な HTTP リクエストを再試行する
tags: [HTTP 再試行, リトライ, 冪等, サーバーエラー, retry, idempotent, fetch, 5xx]
lib: es-toolkit
fn: retry
since: "1.51.0"
verified: 2026-09-17
status: public
---

`fetch` を `retry` で包み、5xx とネットワーク断だけをやり直す。**冪等なリクエスト（GET / PUT / DELETE、または冪等キー付き POST）に限る**。

## Signature

```ts
function retry<T>(func: () => Promise<T>, options: RetryOptions): Promise<T>
// RetryOptions: { retries?: number; delay?: number | ((attempts: number, error: unknown) => number); shouldRetry?: (error: unknown, attempt: number) => boolean; signal?: AbortSignal }
```

## Usage

```ts
import { retry } from 'es-toolkit';

class HttpError extends Error { constructor(public status: number) { super(`HTTP ${status}`); this.name = 'HttpError'; } }
const res = await retry(async () => {
  const res = await fetch('https://example.com/items/1', { method: 'GET', signal });
  if (!res.ok) throw new HttpError(res.status);   // fetch は 4xx / 5xx で reject しないので自分で投げる
  return res;
}, { retries: 3, delay: 500, shouldRetry: (e) => e instanceof TypeError || (e instanceof HttpError && e.status >= 500) });
// => 2xx の Response。4xx は 1 回で HttpError、5xx が 4 回続いたら最後の HttpError
```

## Contract

- `fetch` はレスポンスが届けば **ステータスに関わらず resolve** する。再試行させるには `res.ok` を見て自分で throw する
- ネットワーク断（接続拒否・DNS 失敗）は `TypeError`（message `fetch failed`、原因は `cause`）で reject する。`shouldRetry` で `TypeError` を再試行対象にすると拾える
- `shouldRetry(error, attempt)` が `false` を返した時点でそのエラーを投げ、それ以上 `fetch` を呼ばない。4xx を除外すればクライアント側の誤りで無駄に叩かない
- `retries` は再試行の回数で、合計 `retries + 1` 回まで `fetch` を呼ぶ。全部失敗したら最後のエラーを投げる
- `signal` を `fetch` に渡すと進行中のリクエストが中断され `AbortError`（`DOMException`）で reject する。同じ `signal` を `retry` にも渡すと次の試行に入らない（待機中は止まらない。カード async-retry）
- 各試行で `fetch` を呼び直すので `Request` オブジェクトの使い回しは不要。本文が `ReadableStream` の場合は 2 回目に送れないので、試行ごとに生成する

## Alternatives

- 429 / 503 の `Retry-After` を尊重した指数バックオフはカード http-rate-limit-backoff
- 1 回ごとに制限時間を付けるなら `fetch(url, { signal: AbortSignal.timeout(ms) })`（カード http-timeout）を `func` の中に書く
- ヘッダー判定・バックオフ・冪等キーまで込みで欲しいなら `ky`（`retry` オプション）や `got`

## Pitfalls

- 冪等でない POST（注文・送金・投稿）を再試行すると **二重実行** になる。サーバーが冪等キー（`Idempotency-Key` ヘッダーなど）を受け付ける場合だけ再試行する
- 「レスポンスを受け取る前に切れた」のか「サーバーが処理したあとに切れた」のかは `TypeError` からは区別できない。冪等性はサーバー側で担保する
- 4xx（特に 401 / 403 / 404 / 422）を再試行しても結果は変わらない。`408`（Request Timeout）だけは再試行してよい
- `Response` を返して本文を読まずに捨てると接続が残る。使わない `Response` は `await res.body?.cancel()` で解放する
- `delay` を 0 のまま再試行すると障害中のサーバーを連打する。最低でも数百 ms、できれば指数バックオフを付ける

## Test

`examples/http-retry-idempotent.test.ts`
