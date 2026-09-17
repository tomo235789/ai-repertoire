---
id: number-clamp
lang: typescript
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: es-toolkit
fn: clamp
since: "1.0.0"
verified: 2026-09-17
status: public
---

数値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。

## Signature

```ts
function clamp(value: number, maximum: number): number
function clamp(value: number, minimum: number, maximum: number): number
```

## Usage

```ts
import { clamp } from 'es-toolkit';

clamp(120, 0, 100); // => 100
clamp(-5, 0, 100);  // => 0
clamp(42, 0, 100);  // => 42
clamp(120, 100);    // => 100（引数 2 個なら上限のみ）
```

## Contract

- 引数 3 個 `clamp(value, min, max)` は `Math.min(Math.max(value, min), max)`。境界値は含む（`clamp(0, 0, 100)` は `0`）
- 引数 2 個 `clamp(value, max)` は `Math.min(value, max)`。下限は設けない（負数もそのまま返る）
- 第 3 引数が `undefined` または `null` なら 2 個の形式として扱う
- `min > max` の場合は常に `max` が返る（`Math.min` が最後に適用されるため）
- どれか 1 つでも `NaN` なら `NaN` を返す
- 純粋関数。引数を変更せず、例外は投げない

## Alternatives

- stdlib の `Math.min(Math.max(v, lo), hi)` で足りる。可読性と引数順の間違い防止のために使う
- 範囲内かの判定だけなら `inRange(value, min, max)`
- lodash からの移行は `es-toolkit/compat` の `clamp`（`NaN` の境界を `0` として扱う）

## Pitfalls

- lodash の `clamp(5, NaN, 10)` は `NaN` を `0` とみなして `5` だが、es-toolkit は `NaN` を返す
- `min > max` の検証はしないので、引数の順序を取り違えると常に `max` が返り気付きにくい
- 2 引数形式は上限のみ。`clamp(value, min)` で「下限のみ」にはならない
- Python には標準の clamp が無く `max(lo, min(v, hi))` と書く。引数順（value が先）が異なる

## Test

`examples/number-clamp.test.ts`
