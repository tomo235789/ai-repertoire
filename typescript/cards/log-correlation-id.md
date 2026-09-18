---
id: log-correlation-id
lang: typescript
title: リクエスト ID を非同期処理の連鎖に引き回す
tags: [リクエスト ID, 相関 ID, トレース, コンテキスト伝搬, correlation-id, request-id, AsyncLocalStorage, context]
lib: node:async_hooks
fn: AsyncLocalStorage
since: "Node 16"
verified: 2026-09-17
status: public
---

`als.run(id, handler)` で始めた処理の中では、どれだけ `await` や `setTimeout` を挟んでも `als.getStore()` が同じ `id` を返す。引数で引き回さずにログへリクエスト ID を付けるために使う。

## Signature

```ts
class AsyncLocalStorage<T> {
  run<R>(store: T, callback: (...args: any[]) => R, ...args: any[]): R;
  getStore(): T | undefined;
  exit<R>(callback: (...args: any[]) => R, ...args: any[]): R;
}
```

## Usage

```ts
import { AsyncLocalStorage } from 'node:async_hooks';

const requestId = new AsyncLocalStorage<string>();
const log = (msg: string) => console.log(JSON.stringify({ requestId: requestId.getStore(), msg }));
await requestId.run('req-1', async () => {
  log('start');                                 // => {"requestId":"req-1","msg":"start"}
  await new Promise((r) => setTimeout(r, 10));
  log('done');                                  // => {"requestId":"req-1","msg":"done"}（await 越えでも同じ）
});
log('outside');                                 // => {"msg":"outside"}（run の外は undefined）
```

## Contract

- `run(store, callback)` は `callback` を同期的に呼び、その戻り値（`Promise` なら `Promise`）をそのまま返す。`callback` の中と、そこから派生した非同期処理（`await` の続き、`setTimeout` / `setImmediate` / `Promise.then` のコールバック、`callback` 内で `emit` したイベントのリスナー）で `getStore()` が `store` を返す
- `run` の外（呼ぶ前・呼んだあと・別の `run` の中）では `getStore()` は `undefined`（別の `run` ならその `store`）
- 並行する複数の `run` はそれぞれ独立している。`Promise.all` で同時に走らせても混ざらない
- `run` を入れ子にすると内側では内側の `store`、内側の `callback` を抜けると外側の `store` に戻る
- `callback` が同期的に throw した場合は `run` がその例外を投げ、コンテキストは元に戻る
- `exit(callback)` はその中だけ `getStore()` を `undefined` にする。`store` がオブジェクトなら参照共有なので、中で変更すると同じ `run` 内の全箇所に見える

## Alternatives

- HTTP サーバーなら受信ハンドラで `als.run(req.headers['x-request-id'] ?? crypto.randomUUID(), () => next())`。Express / Fastify / Hono にも同等のミドルウェアがある
- 分散トレースまで要るなら OpenTelemetry（`context.active()` は内部で `AsyncLocalStorage` を使う）
- 複数の値を持たせるなら `store` をオブジェクト（`{ requestId, userId }`）にし、`pino` の子ロガーごと入れておく

## Pitfalls

- `run` の外で作った `Promise` を中で `await` しても中の `store` は見える。逆に、中で作ったコールバックを外で呼ぶ（キューに積んで別のループで実行するなど）と伝搬しない。「コールバックが登録された時点」でなく「非同期処理が生成された時点」の文脈が付く
- `als.getStore()` は `undefined` を返し得る。ログ関数側で `requestId ?? 'none'` のように扱う
- `store` を後から差し替える `enterWith(store)` は同期的な呼び出し元にも影響して追いにくい。原則 `run` だけ使う
- `AsyncLocalStorage` は Node 固有。ブラウザには無く、Deno / Bun / Cloudflare Workers はそれぞれ互換実装を持つ（`node:async_hooks` の import で動くが範囲が異なる）
- テストで `run` を忘れると全部 `undefined` で通ってしまう。`getStore()` を検証するテストを 1 つ置く

## Test

`examples/log-correlation-id.test.ts`
