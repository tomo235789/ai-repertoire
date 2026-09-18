---
id: error-assert-never
lang: typescript
title: 分岐の網羅漏れをコンパイル時に検出する
tags: [網羅性チェック, 分岐漏れ, ユニオン型, switch, exhaustive, assertNever, never, discriminated-union]
lib: stdlib
fn: never 型
since: "TypeScript 2.0"
verified: 2026-09-17
status: public
---

`switch` の `default` で `assertNever(x)` を呼び、ユニオン型のケースを全部処理していなければコンパイルエラーにする。型に列挙子を足したときの処理漏れを防ぐために使う。

## Signature

```ts
function assertNever(value: never, message?: string): never
```

## Usage

```ts
function assertNever(value: never): never { throw new Error(`Unexpected value: ${JSON.stringify(value)}`); }
type Shape = { kind: 'circle'; r: number } | { kind: 'square'; s: number };
function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle': return Math.PI * shape.r ** 2;
    case 'square': return shape.s ** 2;
    default: return assertNever(shape); // Shape に 'triangle' を足すと、ここが型エラーになる
  }
}
```

## Contract

- 引数の型が `never`。`switch` / `if` で全ケースを処理し切ると `default` での `shape` は `never` に絞り込まれ、コンパイルが通る。ケースが残っていると残りの型（`{ kind: 'triangle' }` など）が `never` に代入できずエラーになる
- 戻り値の型も `never` なので、`return assertNever(x)` と書けば関数の戻り値型の検査（「すべてのパスで値を返す」）も満たす
- 実行時に呼ばれたら（`as` キャストや JSON など型を通らない値が来た場合）`Error` を投げる。`JSON.stringify(value)` で値をメッセージに含めるので原因を追える
- 網羅漏れの検出は `tsc`（型検査）でのみ起こる。`vitest` はトランスパイルだけなので実行しても検出されず、CI で `tsc --noEmit` を回す必要がある
- テストでは `// @ts-expect-error` を網羅漏れの行に置くと、漏れがある間は通り、漏れを直して型エラーが消えると **逆に** `tsc` が失敗する（`@ts-expect-error` の未使用）

## Alternatives

- `switch` に `default` を置きたくないなら `const _exhaustive: never = shape;` の代入だけでも検出できる（実行時の throw は無い）
- `Record<Shape['kind'], (s: ...) => number>` の辞書に処理を書くと、キーが足りないときにオブジェクトリテラルの型エラーで検出できる
- ESLint の `@typescript-eslint/switch-exhaustiveness-check` は `default` なしの `switch` の漏れを警告する

## Pitfalls

- `default` を `throw new Error('unknown')` だけにすると `never` の検査が無く、列挙子を足しても気付けない
- `switch (shape.kind)` ではなく `switch (true)` や `if (typeof ...)` の複雑な条件では絞り込みが効かず `never` にならない場合がある
- `string` のような開いた型は絞り込んでも `never` にならない。判別可能な共用体（`kind: 'a' | 'b'`）か `enum` にする
- 実行時に届く値は型の外から来る（API 応答・古いデータ）。`assertNever` は最後の砦で、入口ではスキーマ検証（カード http-fetch-json-typed）を行う
- メッセージに `JSON.stringify(value)` を使うと循環参照や `BigInt` で `TypeError` になる。`String(value)` にするか `try` で包む

## Test

`examples/error-assert-never.test.ts`
