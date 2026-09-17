---
id: pattern-memo-callback
lang: react
title: memo 化した子に渡すコールバックを安定させる
tags: [コールバック, 再レンダー抑止, メモ化, 依存配列, useCallback, memo, stable-callback, re-render]
lib: react
fn: useCallback
since: "18.0"
verified: 2026-09-17
status: public
---

`memo` で包んだ子コンポーネントにイベントハンドラを渡すとき。毎レンダー新しい関数を作ると `memo` が効かないので、`useCallback` で依存が変わらない限り同じ関数を渡す。

## Signature

```tsx
function useCallback<F extends (...args: never[]) => unknown>(fn: F, deps: readonly unknown[]): F
function memo<P>(component: (props: P) => JSX.Element): (props: P) => JSX.Element
```

## Usage

```tsx
import { memo, useCallback, useState } from 'react';

const IncrementButton = memo(({ onClick }: { onClick: () => void }) => <button onClick={onClick}>+1</button>);

function Toolbar() {
  const [count, setCount] = useState(0);
  const increment = useCallback(() => setCount((c) => c + 1), []); // 関数型更新なので依存は空でよい
  return <><p>{count}</p><IncrementButton onClick={increment} /></>;
  // => count が変わって Toolbar が再レンダーされても IncrementButton は再レンダーされない
}
```

## Contract

- `useCallback` は依存配列（`Object.is` 比較）が同じ間は同じ関数を返す。`memo` 化した子は props が同じなので、親の無関係な更新で再レンダーされない
- 関数型更新 `setCount((c) => c + 1)` を使えば state に依存しないので依存配列を空にでき、それでも常に最新の state を更新できる
- 依存する値（`id` など）が変わったときだけ新しい関数になり、子はそのとき再レンダーされる。古い値を掴んだままにならない
- 比較: インライン関数（`onClick={() => ...}`）を渡すと毎回別の関数になり、`memo` 化していても子は毎回再レンダーされる
- 依存に入れた props のコールバック自体が毎レンダー新しいと安定しない（呼び出し側でも安定させる必要がある）

## Alternatives

- 子が `memo` 化されておらず、`useEffect` の依存にも入れないなら `useCallback` は不要。素のインライン関数でよい
- 関数だけでなくオブジェクト・配列の props も同じ問題を起こす。`useMemo` で安定させる（カード pattern-derived-state）
- 最新の値を参照しつつ関数の参照を固定したい（イベントハンドラを effect から呼ぶなど）なら `useRef` に最新の関数を入れる（カード pattern-effect-cleanup の `savedCallback`）

## Pitfalls

- React Compiler が有効なプロジェクトでは `useCallback` / `memo` は自動で挿入されるので手書きは原則不要。ただしコンパイラが最適化を諦めた箇所（ルール違反があるコンポーネント）では効かないので、Compiler 前提でも動作の正しさを `useCallback` に依存させない
- 依存配列から値を抜いて安定させると古い値（stale closure）を掴む。lint（`react-hooks/exhaustive-deps`）の指摘は抑止せず、関数型更新か `useRef` で解決する
- `memo` は浅い比較。`children` に JSX を渡すと毎回新しい要素なので効かない

## Test

`examples/pattern-memo-callback.test.tsx`
