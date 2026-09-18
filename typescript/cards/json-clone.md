---
id: json-clone
lang: typescript
title: ネストした値を深く複製する
tags: [深いコピー, ディープクローン, 複製, clone, deep-copy, structuredClone, immutable]
lib: stdlib
fn: structuredClone
since: "ES2022"
verified: 2026-09-17
status: public
---

ネストしたオブジェクト・配列・`Date`・`Map`・`Set` を全階層で複製し、元の値と切り離す。状態のスナップショットや、変更前の値を保存したいときに使う。

## Signature

```ts
function structuredClone<T>(value: T, options?: { transfer?: Transferable[] }): T
```

## Usage

```ts
const src = { when: new Date(0), tags: new Set(['a']), nested: { n: [1, 2] } };
const copy = structuredClone(src);
copy.nested.n.push(3);
src.nested.n;               // => [1, 2]（元は変わらない）
copy.when instanceof Date;  // => true
structuredClone({ fn: () => 1 }); // => throws DOMException（name: 'DataCloneError'）
```

## Contract

- 全階層を新しいオブジェクトとして複製し、元の値は変更しない。戻り値の型は入力と同じ `T`
- `Date` / `RegExp` / `Map` / `Set` / TypedArray / `ArrayBuffer` / `Error` / `bigint` / `NaN` / `-0` / `undefined` を値に持つプロパティを保持する。循環参照と、同じオブジェクトへの複数参照（複製後も同一参照）も構造を保つ
- 関数 / symbol 値 / `WeakMap` / `Promise` / `Proxy` を含むと `DOMException`（`name: 'DataCloneError'`、`code: 25`、`Error` のサブクラス）を投げる。ツリーのどこかに 1 つでもあれば全体が失敗する
- symbol キーのプロパティは黙って落ちる。getter は評価された値がデータプロパティとして複製される
- クラスインスタンスはプロトタイプを失いプレーンオブジェクトになる（メソッド・getter は消える）。`Error` は組み込みの種別（`TypeError` など）は保持するが、独自サブクラスは `Error` になる
- `Object.freeze` した値の複製は凍結されていない
- `RegExp` の `lastIndex` は 0 に戻る
- `{ transfer: [buffer] }` を渡すと `ArrayBuffer` を複製ではなく移動し、元の `byteLength` は 0 になる

## Alternatives

- クラスインスタンス・関数・symbol を含む値は es-toolkit の `cloneDeep`。プロトタイプを保ったまま複製し、関数と symbol は参照のままコピーする。循環参照・`Map` / `Set` / `Date` / `Error` も扱える
- `JSON.parse(JSON.stringify(v))` は `Date` が文字列に、`undefined` が消え、`Map` / `Set` が `{}` になり、循環で `TypeError`。非推奨
- 1 階層だけなら `{ ...obj }` / `[...arr]`

## Pitfalls

- ドメインオブジェクト（クラスインスタンス）を含むツリーに使うとメソッドが消える。`cloneDeep` を使う
- イベントハンドラ入りの設定や React の props のように関数を含むものは `DataCloneError`。複製したい部分だけ切り出すか `cloneDeep` を使う
- `transfer` を指定した `ArrayBuffer` は元が使えなくなる。共有したい場面では指定しない
- 例外の判定は `e instanceof DOMException && e.name === 'DataCloneError'`。`instanceof Error` でも捕まる

## Test

`examples/json-clone.test.ts`
