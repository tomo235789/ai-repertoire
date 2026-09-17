---
id: pattern-context-split
lang: react
title: state と dispatch を別の Context に分けて再レンダーを減らす
tags: [コンテキスト, 状態共有, 再レンダー抑止, リデューサー, createContext, useReducer, dispatch, provider]
lib: react
fn: createContext
since: "19.0"
verified: 2026-09-17
status: public
---

ツリーの深い所から状態を読み書きしたいとき。読む側（state）と更新する側（dispatch）を別の Context にすると、ボタンのように dispatch しか使わないコンポーネントは state が変わっても再レンダーされない。

## Signature

```tsx
function CounterProvider(props: { children: ReactNode; initial?: CounterState }): JSX.Element
function useCounterState(): CounterState
function useCounterDispatch(): Dispatch<CounterAction>
```

## Usage

```tsx
import { createContext, useReducer, type Dispatch, type ReactNode } from 'react';
import { counterReducer, type CounterAction, type CounterState } from './counter'; // 純粋な reducer と型は別モジュール

const StateContext = createContext<CounterState | null>(null);
const DispatchContext = createContext<Dispatch<CounterAction> | null>(null);

function CounterProvider({ children, initial = { count: 0, label: 'counter' } }: { children: ReactNode; initial?: CounterState }) {
  const [state, dispatch] = useReducer(counterReducer, initial);
  return <DispatchContext value={dispatch}><StateContext value={state}>{children}</StateContext></DispatchContext>;
} // => useContext(DispatchContext) だけ使う子は state 更新で再レンダーされない
```

## Contract

- state を使う子は更新のたびに再レンダーされ、dispatch だけ使う子は再レンダーされない（`useReducer` の `dispatch` は同じ参照であり続ける）
- `children` として渡された、Context を使わない要素は Provider の state 更新で再レンダーされない
- 比較: `{ state, dispatch }` を 1 つの Context で配ると、値のオブジェクトが毎回新しくなるため dispatch だけ使う子も毎回再レンダーされる
- reducer は純粋関数で、入力を変更せず新しい state を返す。コンポーネント無しで単体テストできる
- Provider の外でフックを使うと明示的なメッセージの例外を投げる（`null` の既定値をそのまま返さない）

## Alternatives

- 状態が 1 つのサブツリーに閉じるなら Context を使わず props で渡す。Context は「多くの階層を素通りさせる」ためのもの
- 更新頻度が高い・購読を細かく分けたい場合は外部ストア + `useSyncExternalStore`（カード pattern-external-store）や Zustand / Jotai
- React 18 以前は `<Context.Provider value={...}>` と書く（React 19 から `<Context value={...}>` で Provider として使える）

## Pitfalls

- `useState` の setter や `useReducer` の `dispatch` は安定しているが、`{ increment: () => dispatch(...) }` のように毎レンダー作るオブジェクトで包むと安定性が失われる。包むなら `useMemo`
- state 側の Context に `useMemo` 無しで `{ ...state, extra }` を渡すと、state が同じでも参照が変わって全購読者が再レンダーされる
- Context の値が変わると購読しているコンポーネントは `memo` でも再レンダーされる。`memo` は props の比較であって Context は対象外
- state を粒度ごとにさらに分けるかは計測してから決める。Context を増やしすぎると Provider のネストが深くなる

## Test

`examples/pattern-context-split.test.tsx`
