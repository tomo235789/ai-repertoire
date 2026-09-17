---
id: object-invert
lang: typescript
title: オブジェクトのキーと値を入れ替える
tags: [逆引き, キーと値の交換, 逆マッピング, invert, reverse-map, swap-keys, lookup]
lib: es-toolkit
fn: invert
since: "1.0.0"
verified: 2026-09-17
status: public
---

キーと値を入れ替えた新しいオブジェクトを作る。コード → 名前の対応表から名前 → コードの逆引き表を作るときに使う。

## Signature

```ts
function invert<K extends PropertyKey, V extends PropertyKey>(obj: Record<K, V>): Record<V, K>
```

## Usage

```ts
import { invert } from 'es-toolkit';

const codeToName = { 1: 'red', 2: 'blue' };
invert(codeToName);
// => { red: '1', blue: '2' }
```

## Contract

- 入力オブジェクトを変更しない。返り値は新しいオブジェクト
- 返り値のキーは元の値、返り値の値は元のキーを **文字列** にしたもの（数値キー `1` は `'1'` になる）
- 値が重複した場合は `Object.keys` の順で **最後** に処理されたキーが残る。整数風のキーは挿入順ではなく昇順に並ぶため、`{ b: 1, a: 1 }` は `a` が残り、`{ 2: 'x', 1: 'x' }` は `'2'` が残る
- 自身の列挙可能な文字列キーだけを対象にする。継承したプロパティとシンボルキーは無視する
- 空オブジェクトを渡すと `{}` を返す
- 例外は投げない

## Alternatives

- 重複する値をまとめたい（`{ 1: ['a', 'b'] }`）なら `es-toolkit/compat` の `invertBy`
- 依存を増やせない場合のみ stdlib で `Object.fromEntries(Object.entries(obj).map(([k, v]) => [v, k]))`
- オブジェクトなど文字列化できない値をキーにしたいなら `Map` を作る

## Pitfalls

- 元の値が `'__proto__'` のときは返り値のキーとして作られない（プロトタイプ設定として扱われる）

- 型は `Record<V, K>` で元のキーの型（数値キーなら `number`）のままだが、実行時の値は常に文字列。数値に戻すには `Number()` が要る
- 元の値が `undefined` や `null` でも、キー `'undefined'` / `'null'` として入る
- Python の `{v: k for k, v in d.items()}` と同じで最後が残る。ただし Python の dict は挿入順だが、JS は整数風キーが先に昇順で並ぶ

## Test

`examples/object-invert.test.ts`
