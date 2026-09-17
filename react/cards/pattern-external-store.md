---
id: pattern-external-store
lang: react
title: React 外のストアを購読してスナップショットを読む
tags: [外部ストア, 購読, スナップショット, セレクタ, useSyncExternalStore, store, subscribe, getServerSnapshot]
lib: react
fn: useSyncExternalStore
since: "18.0"
verified: 2026-09-17
status: public
---

React の state ではない場所（モジュールスコープのストア、`window.matchMedia`、`localStorage`、`navigator.onLine`）にある値を表示したいとき。`subscribe` と `getSnapshot` を渡して `useSyncExternalStore` で購読する。

## Signature

```tsx
function useSyncExternalStore<S>(subscribe: (onChange: () => void) => () => void, getSnapshot: () => S, getServerSnapshot?: () => S): S
function useStore<T, S = T>(store: Store<T>, selector?: (state: T) => S, getServerSnapshot?: () => T): S
```

## Usage

```tsx
import { useSyncExternalStore } from 'react';

const store = createStore({ theme: 'light', fontSize: 14 }); // subscribe / getSnapshot / setState を持つ

function ThemeLabel() {
  const theme = useSyncExternalStore(store.subscribe, () => store.getSnapshot().theme);
  return <p>{theme}</p>;
  // => store.setState(...) を React の外で呼ぶと再レンダーされる。theme 以外の変更では再レンダーされない
}
```

## Contract

- React 外で `setState` すると、購読しているコンポーネントが再レンダーされて新しい値を表示する
- `getSnapshot`（selector）の結果が `Object.is` で同じ間は再レンダーされない。無関係なフィールドの更新では描画されない
- マウント時に `subscribe` し、アンマウント時に返された関数で解除する。StrictMode でも購読数は 1 に収束し、アンマウント後は 0 になる
- サーバーレンダー（`renderToString`）では `getServerSnapshot` の値が使われる。渡さないと `Missing getServerSnapshot` の例外になる
- `getSnapshot` が毎回新しいオブジェクトを返すと警告（`The result of getSnapshot should be cached`）が出て、`Maximum update depth exceeded` で無限ループになる
- `useStore` はストアのスナップショットが同じ間は selector の結果をキャッシュし、`Object.is` で同じ参照を返す。オブジェクトを作る selector でも無限ループにならない（ただしストアが変わるたびに新しいオブジェクトになり再レンダーされる）

## Alternatives

- 状態が React の中だけで完結するなら `useState` / `useReducer` + Context（カード pattern-context-split）
- Zustand / Redux / Jotai はこのフックを内部で使っている。selector・devtools・永続化が要るならそちら
- `useEffect` + `setState` で購読する旧来の書き方は、レンダーと購読の間に更新が挟まると古い値を表示する（tearing）。React 18 以降は `useSyncExternalStore` に置き換える

## Pitfalls

- `getSnapshot` は不変のスナップショットを返す。`() => ({ ...state })` や `() => list.filter(...)` のように毎回作ると無限ループになる。オブジェクトを返す selector はスナップショットごとに結果をキャッシュする（`useStore` の `cachedSelector`）。再レンダーも抑えたいなら selector でプリミティブに絞るか、ストア側でメモ化する
- `subscribe` 関数をレンダー中に作ると毎回別の関数になり、レンダーごとに購読し直す。モジュールスコープか `useCallback` で固定する
- ストアの更新は同期的にレンダーされる（トランジションにならない）。大きな更新は分割するか `startTransition` の外で行う設計を見直す
- SSR + ハイドレーションでは `getServerSnapshot` がサーバーとクライアント初回で同じ値を返す必要がある。`localStorage` 由来の値は初回はサーバー側の既定値にする

## Test

`examples/pattern-external-store.test.tsx`
