---
id: pattern-fetch-with-abort
lang: react
title: effect でデータを取得し、古いリクエストを abort する
tags: [データ取得, 中断, レース, 競合状態, fetch, AbortController, race-condition, useEffect]
lib: react
fn: useEffect
since: "18.0"
verified: 2026-09-17
status: public
---

props（URL や ID）に応じてデータを取得して表示するとき。依存が変わったら前のリクエストを `AbortController` で中断し、遅れて届いた古いレスポンスで state を上書きしない。

## Signature

```tsx
function useFetch<T>(url: string, fetchFn?: typeof fetch): { status: 'loading' } | { status: 'success'; data: T } | { status: 'error'; error: Error }
```

## Usage

```tsx
import { useEffect, useState } from 'react';
useEffect(() => {
  const controller = new AbortController();
  setState({ status: 'loading' });
  fetch(url, { signal: controller.signal })
    .then((res) => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); }) // 非 2xx は失敗
    .then((data) => { if (!controller.signal.aborted) setState({ status: 'success', data }); })
    .catch((error) => { if (!controller.signal.aborted) setState({ status: 'error', error }); });
  return () => controller.abort(); // url 変更・アンマウントで中断。古い結果は捨てる
}, [url]);
```

## Contract

- マウント時に `signal` 付きで `fetch` を呼び、解決後に `success` になる
- `url` が変わると前のリクエストの `signal` が abort され、state は `loading` に戻る。新しい URL の結果で `success` になる
- 古いレスポンスが後から届いても state を上書きしない。`fetch` が abort を無視して解決した場合でも `signal.aborted` の確認で捨てられる
- アンマウント時に abort し、その後の `AbortError` や解決で state を更新しない（警告も出ない）
- HTTP エラー（`res.ok` が偽）や reject は `error` になる。`AbortError` だけは無視する
- StrictMode（開発時）では effect が 2 回走り `fetch` も 2 回呼ばれるが、1 回目は即座に abort され、2 回目の結果だけが使われる

## Alternatives

- 実務では TanStack Query / SWR などのデータ取得ライブラリを使う。キャッシュ・重複排除・再試行が付き、このパターンは内部で行われる
- フレームワーク（Next.js / Remix）ならサーバー側のローダーや Server Components で取得し、クライアント effect での取得を避ける
- React 19 の `use(promise)` + Suspense はレンダー中に promise を読む形で、`Suspense` の fallback と Error Boundary に統合される

## Pitfalls

- `let ignore = false; return () => { ignore = true }` のフラグ方式でもレースは防げるが、ネットワーク要求自体は続く。`AbortController` なら通信も止まる
- `fetch` の第 2 引数のオブジェクトや `fetchFn` を毎レンダー新しく作って依存に入れると、レンダーのたびに再取得と abort を繰り返す
- `setState({ status: 'loading' })` を effect の外（レンダー中）で呼ばない。effect の先頭で呼ぶか、`url` をキーにして loading を導出する
- `async` 関数を `useEffect` に直接渡さない（戻り値が cleanup ではなく Promise になる）

## Test

`examples/pattern-fetch-with-abort.test.tsx`
