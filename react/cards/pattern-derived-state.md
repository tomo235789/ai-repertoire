---
id: pattern-derived-state
lang: react
title: state から導出できる値をレンダー中に計算する
tags: [導出状態, 派生値, 計算, 同期effect, derived-state, computed, useMemo, no-effect-sync]
lib: react
fn: レンダー時の計算
since: "18.0"
verified: 2026-09-17
status: public
---

合計・フィルタ結果・表示用の整形など、props や state から計算できる値を持ちたいとき。別の state にコピーせず、レンダー中に計算する。高コストなら `useMemo` で結果を持ち越す。

## Signature

```tsx
function Total(props: { items: readonly Item[] }): JSX.Element
function useMemo<T>(factory: () => T, deps: readonly unknown[]): T
```

## Usage

```tsx
import { useMemo } from 'react';

function Total({ items, query }: { items: Item[]; query: string }) {
  const total = items.reduce((sum, it) => sum + it.price, 0); // 毎レンダー計算。state にしない
  const filtered = useMemo(() => items.filter((it) => it.name.includes(query)), [items, query]);
  return <p>{filtered.length} 件 / 合計 {total}</p>;
  // => props が変わったその同じレンダーで正しい値になる。useEffect + setState は不要
}
```

## Contract

- レンダー中に計算した値は最初のレンダーから正しく、レンダーは 1 回で済む。props が変わっても同じレンダーで新しい値になる
- `useMemo` は依存配列（`Object.is` 比較）が同じ間は通常は再計算を省略して前回の結果を返す最適化。親の無関係な更新で再レンダーされても普通は factory は呼ばれないが、React はこれを保証しない（メモを破棄して再計算することがある）。依存が変わったときは必ず再計算する
- 依存に毎レンダー新しい配列・オブジェクトを渡すと毎回再計算される
- 比較: `useEffect` で `setState` に同期するとマウント時は初期値（`0` など）で 1 回描画してから正しい値で再描画され、更新時も古い値で 1 回描画してから追いつく（1 レンダー遅れ、レンダー回数が倍になる）

## Alternatives

- 「props が変わったら state をリセットしたい」なら `useEffect` ではなく親で `key` を変えて作り直す（カード pattern-list-keys）
- 計算結果を複数コンポーネントで共有するなら Context か外部ストアの selector（カード pattern-external-store）
- React Compiler を有効にしていれば `useMemo` 相当のメモ化は自動で入る。手書きの `useMemo` は残しても害は無い

## Pitfalls

- `useMemo` はパフォーマンス最適化であって意味論の保証ではない。React は将来メモを破棄してよいとしているので、`useMemo` 無しでも正しく動く書き方にする
- 「同期 effect」は 1 レンダー遅れるだけでなく、依存の網羅漏れで古い値が残るバグの温床になる。`useEffect` の中に `setState` しか無いなら導出に置き換える
- 導出のためのコピー state（`const [total, setTotal] = useState(props.total)`）は props の更新に追随しない。初期値としてしか使われない

## Test

`examples/pattern-derived-state.test.tsx`
