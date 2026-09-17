---
id: pattern-list-keys
lang: react
title: リストの要素に安定した一意な key を付ける
tags: [リスト, キー, 一意性, 並べ替え, 状態リセット, key, list-rendering, reconciliation]
lib: react
fn: key
since: "18.0"
verified: 2026-09-17
status: public
---

配列を `map` して要素を並べるとき。`key` にはデータの ID など、並べ替え・削除をまたいで同じ要素を指す値を使う。配列の index は「その位置」を指すだけなので、要素の状態（入力欄の内容やフォーカス）が別のデータに付いてしまう。

## Signature

```tsx
function EditableRows(props: { rows: readonly { id: string; label: string }[] }): JSX.Element
<Child key={string | number} />
```

## Usage

```tsx
type Row = { id: string; label: string };
function EditableRows({ rows }: { rows: Row[] }) {
  return (
    <ul>
      {rows.map((row) => (
        <li key={row.id}><label>{row.label}<input defaultValue="" /></label></li> // index ではなく id
      ))}
    </ul>
  ); // => 並べ替え・削除しても各 input の内容は同じ row に付いていく
}
```

## Contract

- `id` を `key` にすると、並べ替えても要素の状態（入力欄の内容）は同じ行に付いていく。先頭を削除しても残りの行の状態は保たれ、削除した行だけがアンマウントされる
- index を `key` にすると、並べ替えで入力の状態が別の行に付く（位置 0 の DOM がそのまま使い回され、ラベルだけ変わる）。先頭を削除すると末尾の要素がアンマウントされ、入力の状態が 1 つずつずれる
- `key` を変えると同じ位置でも別の要素として作り直され、state がリセットされる（`<Editor key={userId} />` で切り替え時に初期化できる）
- 兄弟間で `key` が重複すると React が警告する（`Encountered two children with the same key`）

## Alternatives

- データに ID が無い場合は取り込み時に `crypto.randomUUID()` などで ID を付与して保持する。レンダー中に生成すると毎回変わって全要素が再マウントされる
- 並べ替え・削除・挿入が無い静的なリスト（固定の選択肢など）なら index でも実害は無いが、後で編集可能になったときに壊れるので ID を推奨
- 「props が変わったら state をリセットしたい」は `useEffect` ではなく `key` の変更で行う（カード pattern-derived-state）

## Pitfalls

- `key={Math.random()}` や `key={JSON.stringify(row)}` は毎レンダー変わり、全要素がアンマウント → マウントされて状態を失い遅くなる
- `key` は兄弟間で一意であればよく、グローバルに一意である必要は無い。別のリストで同じ ID を使ってよい
- `key` は props としてコンポーネントに渡らない。値が必要なら別の prop（`id`）でも渡す
- `Fragment` で複数要素を返すときは `<Fragment key={...}>` を使う（短縮記法 `<>` に `key` は付けられない）

## Test

`examples/pattern-list-keys.test.tsx`
