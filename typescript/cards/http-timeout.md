---
id: http-timeout
lang: typescript
title: HTTP リクエストに制限時間を設ける
tags: [HTTP タイムアウト, 制限時間, 中断, キャンセル, timeout, fetch, AbortSignal, deadline]
lib: stdlib
fn: AbortSignal.timeout
since: "Node 18"
verified: 2026-09-17
status: public
---

`fetch` に `AbortSignal.timeout(ms)` を渡し、`ms` 以内に終わらなければリクエストを中断して `TimeoutError` で reject させる。応答しないサーバーで待ち続けないために使う。

## Signature

```ts
static AbortSignal.timeout(milliseconds: number): AbortSignal
static AbortSignal.any(signals: AbortSignal[]): AbortSignal
```

## Usage

```ts
try {
  const res = await fetch('https://example.com/items', { signal: AbortSignal.timeout(3_000) });
  const body = await res.json(); // 本文の読み取り中も同じ制限時間が効く
} catch (err) {
  if (err instanceof DOMException && err.name === 'TimeoutError') console.log('3 秒以内に終わらなかった');
  else throw err;
}
// 外部キャンセルと併用: fetch(url, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(3_000)]) })
```

## Contract

- `AbortSignal.timeout(ms)` を作った時点から数え、`ms` 経過で abort する。`signal.reason` は `name` が `'TimeoutError'` の `DOMException`（`code` は 23）。`fetch` はこの `reason` をそのまま投げる
- 制限時間は **接続からレスポンス本文の読み終わりまで** 通しで効く。ヘッダーが届いて `fetch` が resolve したあと、`res.text()` / `res.json()` の途中でも `ms` を超えれば `TimeoutError` で reject する
- 中断されると接続は閉じられ、サーバー側でも切断として観測できる（`req.on('close')` / `req.aborted`）
- `AbortSignal.any([a, b])` はどちらかが abort した時点で abort し、`reason` は先に abort した方のものになる。手動の `controller.abort()` なら `name` が `'AbortError'`
- 既に abort 済みの `signal` を渡すと `fetch` は接続せずに `reason` で reject する
- 接続拒否や DNS 失敗は `TypeError`（message `fetch failed`）で、タイムアウトとは別のエラー。サーバーが 4xx / 5xx を返した場合は resolve する

## Alternatives

- `Promise` を返す処理全般に制限時間を付けるなら `withTimeout`（カード async-timeout。処理自体は止まらない）
- 「接続まで」「ヘッダーまで」「本文の各チャンク間」を分けて制限したいなら `undici` の `Agent({ connectTimeout, headersTimeout, bodyTimeout })`
- Node 18 未満や古いブラウザでは `AbortController` + `setTimeout(() => controller.abort(), ms)`

## Pitfalls

- 判定は `err.name === 'TimeoutError'` で行う。`err.message` は `'The operation was aborted due to timeout'` で環境により変わる
- `AbortSignal.timeout` は生成時から数える。`fetch` を呼ぶ前に作って待たせると、その分だけ実質の制限時間が短くなる
- es-toolkit の `TimeoutError` は `name` が `'Error'` で別物。両方使うなら `instanceof` と `name` の判定を混同しない
- 本文の読み取りまで含めて `ms` なので、大きなレスポンスを受けるときはストリーミングの所要時間も見込んで設定する
- `AbortSignal.timeout` のタイマーはイベントループを止めない（`unref` 済み）。`fetch` が先に終わってもプロセスの終了を `ms` まで待たせることはない

## Test

`examples/http-timeout.test.ts`
