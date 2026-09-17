---
id: string-truncate
lang: csharp
title: 長い文字列を省略記号付きで切り詰める
tags: [切り詰め, 省略, 文字数制限, 省略記号, truncate, ellipsis, clip, shorten]
lib: stdlib
fn: 範囲演算子
since: "6.0"
verified: 2026-09-17
status: public
---

文字列が上限を超えるとき、末尾を省略記号に置き換えて上限に収める。一覧表示のタイトルや通知本文の切り詰めに使う。標準にも MoreLINQ にも専用の関数は無いので、範囲演算子で 1 行のイディオムとして書く。

## Signature

```csharp
s.Length <= n ? s : s[..(n - 3)] + "..."
```

## Usage

```csharp
using System;

static string Truncate(string s, int n) => s.Length <= n ? s : s[..(n - 3)] + "...";

var text = "The quick brown fox jumps over the lazy dog";
Truncate(text, 20);   // => "The quick brown f..."
Truncate("abcde", 5); // => "abcde"（上限以下なら変更しない）
Truncate("abcde", 3); // => "..."
```

## Contract

- `n` は **省略記号を含めた** 結果の最大長。切り詰めたとき結果はちょうど `n` 文字で、先頭 `n - 3` 文字 + `"..."`
- `s.Length <= n` なら `s` をそのまま（同じインスタンス）返す
- 切り詰めが必要で `n < 3` なら `s[..(n - 3)]` が負の長さになり `ArgumentOutOfRangeException`。`n == 3` なら `"..."` だけを返す
- 長さは UTF-16 コード単位で数える。切る位置がサロゲートペアの途中だと高サロゲートだけが残り、UTF-8 に変換すると U+FFFD（`EF BF BD`）になる
- `s` が `null` なら `NullReferenceException`
- 純粋関数。新しい文字列を返し、入力を変更しない

## Alternatives

- 省略記号を 1 文字の `"…"`（U+2026）にするなら `s[..(n - 1)] + "…"`
- 中間文字列を作らないなら `string.Concat(s.AsSpan(0, n - 3), "...")`
- 書記素（結合文字・絵文字）を分断しないなら `new StringInfo(s).SubstringByTextElements(0, k)`、コードポイント単位なら `s.EnumerateRunes()` で `k` 個取って `string.Concat`
- 単語境界で切るなら `s.LastIndexOf(' ', n - 3)` で位置を探してから切る
- MoreLINQ には文字列の切り詰めは無い。`Take` で `char` を数えても同じサロゲートの問題がある

## Pitfalls

- TypeScript（es-toolkit/compat の `truncate`）は `length` の既定が 30 で、サロゲートペアを含む文字列はコードポイントで数える。このイディオムは常に UTF-16 コード単位。絵文字を含む入力があるなら `StringInfo` を使う
- Python の `textwrap.shorten` は連続空白をまとめて単語境界で切る。このイディオムは文字位置で切り、空白もそのまま
- `s[..n]` は `n > s.Length` で `ArgumentOutOfRangeException`。必ず `Length` の判定を先に書く（`Substring` も同じ）
- `"..."`（3 文字）と `"…"`（1 文字）で `n` から引く長さが変わる。省略記号を変えるときは引き算も直す

## Test

`examples/StringTruncateTests.cs`
