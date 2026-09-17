---
id: number-clamp
lang: csharp
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: stdlib
fn: Math.Clamp
since: "6.0"
verified: 2026-09-17
status: public
---

数値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。

## Signature

```csharp
public static int Clamp(int value, int min, int max)
```

## Usage

```csharp
using System;

Math.Clamp(120, 0, 100);   // => 100
Math.Clamp(-5, 0, 100);    // => 0
Math.Clamp(42, 0, 100);    // => 42
Math.Clamp(1.5, 0.0, 1.0); // => 1（double / decimal / long などの多重定義がある）
```

## Contract

- 境界値は含む（`Math.Clamp(0, 0, 100)` は `0`、`Math.Clamp(100, 0, 100)` は `100`）
- `min > max` なら `value` に関係なく `ArgumentException` を投げる。引数順の取り違えがその場で分かる
- `value` が `NaN` なら `NaN` を返す。`min` や `max` が `NaN` のときは比較が常に偽になりその境界だけが効かない（`Math.Clamp(-1.0, double.NaN, 10.0)` は `-1`、`Math.Clamp(15.0, 0.0, double.NaN)` は `15`）
- 返り値は 3 つの引数のいずれかの値。型変換はせず、`int` と `double` を混ぜると暗黙変換で `double` の多重定義が選ばれる（`Math.Clamp(5, 1, 3.5)` は `3.5`）
- 純粋関数。引数を変更しない

## Alternatives

- .NET 7 以降はジェネリック数学の `int.Clamp(v, lo, hi)` / `double.Clamp(...)`（`INumber<T>.Clamp`）。ジェネリックメソッドの中で型に依存せず書ける
- `Math.Min(Math.Max(v, lo), hi)` でも同じだが、`lo > hi` では例外にならず常に `hi` が返る
- 上限だけなら `Math.Min(v, hi)`、下限だけなら `Math.Max(v, lo)`
- 範囲内かの判定だけなら `lo <= v && v <= hi`

## Pitfalls

- TypeScript（es-toolkit の `clamp`）と Python の `min(max(x, lo), hi)` は `min > max` でも例外を出さず `max` を返すが、`Math.Clamp` は `ArgumentException`。移植すると入力次第で落ちる
- es-toolkit の `clamp` はどれか 1 つでも `NaN` なら `NaN` を返すが、`Math.Clamp` は `value` が `NaN` のときだけ。Python と同じく境界に `NaN` が混ざっても気付けない
- es-toolkit の 2 引数形式 `clamp(value, max)` に相当する多重定義は無い。`Math.Min(v, hi)` を使う
- 引数の型を揃えないと意図しない多重定義が選ばれる。`byte` 同士なら `byte` が返り、`int` と `double` が混ざると `double` になる

## Test

`examples/NumberClampTests.cs`
