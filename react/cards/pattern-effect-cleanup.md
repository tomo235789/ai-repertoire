---
id: pattern-effect-cleanup
lang: react
title: effect で始めた購読やタイマーを cleanup で止める
tags: [副作用, 後始末, 購読, タイマー, useEffect, cleanup, subscription, setInterval]
lib: react
fn: useEffect
since: "18.0"
verified: 2026-09-17
status: public
---

`setInterval`・イベントリスナー・WebSocket など、開始したら止める必要がある処理をコンポーネントに紐づけるとき。effect の戻り値で必ず後始末し、依存が変わっても二重に動かない形にする。

## Signature

```tsx
function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void
function useInterval(callback: () => void, delayMs: number | null): void
```

## Usage

```tsx
import { useEffect, useRef } from 'react';
function useInterval(callback: () => void, delayMs: number | null) {
  const saved = useRef(callback);
  useEffect(() => { saved.current = callback; }, [callback]); // 最新の callback を保持
  useEffect(() => {
    if (delayMs === null) return;
    const id = setInterval(() => saved.current(), delayMs);
    return () => clearInterval(id); // アンマウント時・delayMs 変更時に必ず止まる
  }, [delayMs]);
}
```

## Contract

- effect はマウント後（コミット後）に走る。レンダー中には走らない
- アンマウント時に cleanup が走り、以後タイマーは発火せず購読も解除される
- 依存（`delayMs`、`source`）が変わると、前回の cleanup → 新しい effect の順に走る。古いタイマー・購読は残らない
- `delayMs` が `null` なら effect は何もせずタイマーを張らない（条件付きで止められる）
- `callback` を差し替えてもタイマーは張り直されない（`useRef` に最新を入れる）。次の発火から新しい `callback` が使われる
- StrictMode（開発時）ではマウント直後に effect → cleanup → effect と 1 回余分に走る。cleanup が正しければ購読数は 1 に収束し、アンマウント後は 0 になる

## Alternatives

- 外部ストアの購読で「値をレンダーに使いたい」なら `useSyncExternalStore`（カード pattern-external-store）。`useEffect` + `setState` より tearing が起きない
- データ取得は `AbortController` で中断する形にする（カード pattern-fetch-with-abort）
- DOM の測定など描画前に同期して走らせたい処理だけ `useLayoutEffect`。cleanup の規則は同じ

## Pitfalls

- cleanup を書かないと StrictMode で購読が 2 本になり、本番でも依存が変わるたびに増える。「StrictMode で二重に動く」は cleanup 漏れのサインであって React のバグではない
- effect 内で `setInterval(callback, ...)` と直接渡すと `callback` を依存に入れる必要があり、親が再レンダーするたびにタイマーが張り直される。`useRef` で最新を持つ
- 依存配列を空にして古い props を掴む（stale closure）のと、依存を入れて毎回張り直すのはどちらも誤り。「開始と停止に本当に必要な値」だけを依存にする
- 非同期処理の完了後に `setState` するなら cleanup で「もう無効」のフラグを立てるか abort する

## Test

`examples/pattern-effect-cleanup.test.tsx`
