---
id: function-pipe
lang: typescript
title: 複数の関数を左から順に合成する
tags: [関数合成, パイプライン, 左から右, 合成, pipe, compose, flow]
lib: es-toolkit
fn: flow
since: "1.22.0"
verified: 2026-09-17
status: public
---

関数の列を「左から順に前の結果を次に渡す」1 つの関数にまとめる。変換ステップを名前付き関数に分けて読みやすくするのに使う。

## Signature

```ts
function flow<A extends any[], R1, R2>(f1: (...args: A) => R1, f2: (a: R1) => R2): (...args: A) => R2
function flow(...funcs: Array<(...args: any[]) => any>): (...args: any[]) => any // 1〜5 関数は型付きのオーバーロードあり
```

## Usage

```ts
import { flow } from 'es-toolkit';

const add = (a: number, b: number) => a + b;
const double = (n: number) => n * 2;
const toLabel = (n: number) => `total: ${n}`;
const summarize = flow(add, double, toLabel);
summarize(1, 2);
// => 'total: 6'
```

## Contract

- 最初の関数だけが呼び出し時の全引数を受け取り、以降の関数は直前の戻り値 1 つを受け取る。左から順に同期的に実行する
- 関数を 0 個で `flow()` したときは、呼び出しの第 1 引数をそのまま返す
- 5 個までは引数と戻り値の型が推論される。6 個以上は `any` になる
- 呼び出し時の `this` をすべての関数に渡す
- 非同期関数を混ぜても `await` しない。`Promise` がそのまま次の関数に渡される
- 渡された関数を変更せず、合成結果は新しい関数

## Alternatives

- 右から左に合成したい（数学的な `f(g(x))` の順）なら `flowRight`。引数順が逆になるだけで挙動は同じ
- 値を先に渡して `pipe(value, f, g)` の形で書きたいなら `es-toolkit/fp` の `pipe`
- 依存を増やせない場合は `(a, b) => toLabel(double(add(a, b)))` と直接ネストする
- lodash からの移行は `es-toolkit/compat` の `flow`（配列で関数を渡せる）

## Pitfalls

- 非同期のステップを混ぜると 2 つ目以降が `Promise` を受け取って壊れる。非同期パイプラインは `async` 関数の中で `await` を並べるか、各ステップを `async (p) => f(await p)` にする
- lodash の `flow([f, g])` のような配列渡しは不可。可変長引数で渡す
- 2 番目以降の関数に複数の引数を渡したいなら、直前の関数でタプルやオブジェクトに束ねる

## Test

`examples/function-pipe.test.ts`
