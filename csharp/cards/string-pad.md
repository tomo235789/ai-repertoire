---
id: string-pad
lang: csharp
title: 文字列を指定幅まで両側に埋める
tags: [パディング, 中央揃え, 固定幅, 文字埋め, pad, padding, center, fixed-width]
lib: stdlib
fn: String.PadLeft
since: "6.0"
verified: 2026-09-17
status: public
---

文字列の左（または右）に文字を詰めて指定の長さにする。固定幅のテキスト表示やログの桁揃えで使う。**両側に振り分ける中央寄せは標準に無い**。

## Signature

```csharp
public string PadLeft(int totalWidth, char paddingChar)
```

## Usage

```csharp
using System;

"abc".PadLeft(6);             // => "   abc"
"abc".PadRight(6, '*');       // => "abc***"
"abc".PadLeft(2);             // => "abc"（totalWidth が短ければそのまま）
5.ToString().PadLeft(3, '0'); // => "005"
```

## Contract

- 左に `paddingChar`（既定は半角スペース）を詰めて長さ `totalWidth` にする。`PadRight` は右に詰める。新しい文字列を返し、元の文字列は変わらない（`string` は不変）
- `totalWidth` が `Length` 以下（`0` を含む）なら元の文字列をそのまま返す。切り詰めない
- `totalWidth` が負なら `ArgumentOutOfRangeException`
- `paddingChar` は `char` なので 1 文字のみ。複数文字のパターンでは埋められない
- 長さは UTF-16 コード単位で数える。サロゲートペア（絵文字など）は 2、結合文字（`e` + U+0301）は 2、全角文字は 1
- 空文字を渡すと `paddingChar` だけで `totalWidth` を埋める
- 純粋関数。カルチャに依存しない

## Alternatives

- 中央寄せは `s.PadLeft((width + s.Length) / 2).PadRight(width)`。余りが奇数なら右側が 1 文字多くなり、es-toolkit の `pad` と同じ結果
- 補間文字列の配置指定 `$"{s,6}"`（右寄せ）/ `$"{s,-6}"`（左寄せ）。`string.Format("{0,6}", s)` でも同じ
- 数値のゼロ埋めは `n.ToString("D3")`（符号を先頭に保つ。`(-5).ToString("D3")` は `"-005"`）
- 表示幅で揃えたいなら `System.Globalization.StringInfo` で書記素を数えるか、東アジア幅の判定を自前で書く

## Pitfalls

- TypeScript（es-toolkit の `pad`）と Python の `str.center` は両側に詰めるが、`PadLeft` / `PadRight` は片側だけ。中央寄せは Alternatives のイディオムで組む
- `(-5).ToString().PadLeft(4, '0')` は `"00-5"` になる。符号付きの数値は `ToString("D3")` を使う
- Python の `str.center` はコードポイント、C# は UTF-16 コード単位で数える。絵文字 1 つで幅が 1 ずれる
- 全角文字も 1 と数えるので等幅表示は揃わない。表示幅は別途計算する

## Test

`examples/StringPadTests.cs`
