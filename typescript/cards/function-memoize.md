---
id: function-memoize
lang: typescript
title: 関数の戻り値を引数ごとにキャッシュする
tags: [メモ化, キャッシュ, 計算結果の再利用, memoize, memoization, cache, memo]
lib: es-toolkit
fn: memoize
since: "1.16.0"
verified: 2026-09-17
status: public
---

同じ引数での呼び出し結果をキャッシュし、2 回目以降は関数を実行せずに返す。重い純粋関数（パース・集計・正規化）の再計算を避けるのに使う。

## Signature

```ts
function memoize<F extends (...args: any) => any>(fn: F, options?: { cache?: MemoizeCache<any, ReturnType<F>>; getCacheKey?: (args: Parameters<F>[0]) => unknown }): F & { cache: MemoizeCache<any, ReturnType<F>> }
```

## Usage

```ts
import { memoize } from 'es-toolkit';

const area = memoize((r: number) => { console.log('calc'); return Math.PI * r * r; });
area(2); // 'calc' が出て 12.566...
area(2); // キャッシュから 12.566...（'calc' は出ない）
area.cache.clear(); // キャッシュを消す
const byId = memoize((u: { id: number }) => u.id * 10, { getCacheKey: (u) => u.id });
byId({ id: 1 }) === byId({ id: 1 }); // => true（別オブジェクトでも id が同じなら同じキー）
```

## Contract

- キャッシュキーは **第 1 引数そのもの**。`getCacheKey` を渡すとその戻り値がキーになる
- `fn` には第 1 引数だけが渡される。第 2 引数以降は無視され、キーにも含まれない
- キーの比較は `Map` と同じ SameValueZero。オブジェクトや配列は参照で比較されるので、内容が同じでも別オブジェクトなら別キー
- キャッシュに無いときだけ `fn` を呼び、戻り値を保存してから返す。`fn` が例外を投げた場合は保存しない（次回また呼ばれる）
- `cache` オプションで `Map` 互換（`get` / `set` / `has` / `delete` / `clear` / `size`）の任意のキャッシュに差し替えられる。渡したオブジェクトがそのまま `memoized.cache` として公開される
- 呼び出し時の `this` を保持して `fn` に渡す。`fn` 自体は変更しない

## Alternatives

- 引数無しの初期化を 1 回だけ走らせたいなら `once`（カード function-once）
- 複数引数をキーにしたい場合、`getCacheKey` も第 1 引数しか受け取らないので解決にならない。引数を 1 つのオブジェクト・タプルに束ねてから `memoize` し、`getCacheKey` で `JSON.stringify` する
- サイズ上限・TTL が要るなら `cache` に LRU 実装（`lru-cache` など）を渡す
- lodash からの移行は `es-toolkit/compat` の `memoize`（`resolver` が全引数を受け取る）

## Pitfalls

- 引数が 2 つ以上ある関数をそのままメモ化すると、第 2 引数が `undefined` で呼ばれる上に第 1 引数だけで結果が使い回される。lodash の `memoize` は全引数を渡すので挙動が違う
- lodash の `resolver` は `(...args)` だが、es-toolkit の `getCacheKey` は第 1 引数しか受け取らない
- キャッシュは無制限に増える。ユーザー入力など値域が広い引数をキーにするとメモリリークになる
- 非純粋な関数（時刻や乱数、外部状態に依存）をメモ化すると古い値を返し続ける

## Test

`examples/function-memoize.test.ts`
