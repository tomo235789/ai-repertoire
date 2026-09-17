---
id: string-pad
lang: typescript
title: 文字列を指定幅まで両側に埋める
tags: [パディング, 中央揃え, 固定幅, 文字埋め, pad, padding, center, fixed-width]
lib: es-toolkit
fn: pad
since: "1.0.0"
verified: 2026-09-17
status: public
---

文字列の左右に文字を詰めて指定の長さにする。固定幅のテキスト表示やログの桁揃えで使う。

## Signature

```ts
function pad(str: string, length: number, chars?: string): string
```

## Usage

```ts
import { pad } from 'es-toolkit';

pad('abc', 8);       // => '  abc   '
pad('abc', 8, '_-'); // => '_-abc_-_'
pad('abc', 2);       // => 'abc'
```

## Contract

- 左右に `chars`（既定は半角スペース）を詰めて長さ `length` にする。余りが奇数なら右側が 1 文字多い（`pad('abc', 4)` → `'abc '`）
- `length` が `str.length` 以下（`0`、負数、`NaN` を含む）なら元の文字列をそのまま返す。切り詰めない
- `chars` が複数文字なら左右それぞれの端から繰り返し、端数は切り落とす（`'_-'` で右に 3 文字埋めると `'_-_'`）
- `chars` が空文字なら元の文字列を返す
- 長さは UTF-16 コード単位で数える。サロゲートペア（絵文字など）は 2 として数える
- 空文字を渡すと `chars` だけで `length` を埋める
- 純粋関数。実現可能な `length` の範囲では例外を投げない（`Infinity` や文字列の最大長を超える値は `padStart` / `padEnd` が `RangeError` を投げる）

## Alternatives

- 片側だけ埋めるなら stdlib の `String.prototype.padStart` / `padEnd`（依存不要）
- 数値のゼロ埋めは `String(n).padStart(2, '0')`
- lodash 互換（数値など非文字列も文字列化して受け付ける）は `es-toolkit/compat` の `pad`

## Pitfalls

- `padStart` / `padEnd` は片側にだけ詰めるが、`pad` は両側に振り分ける。両側の詰め方は「左を `padStart`、次に右を `padEnd`」なので、左側の `chars` の並びは左端から始まる
- Python の `str.center` は余り 1 文字をどちらに寄せるかが幅の偶奇で変わる（`'ab'.center(5)` → `'  ab '`）。`pad` は常に右側
- 全角文字も 1 と数えるので表示幅は揃わない。等幅表示で揃えたい場合は表示幅を別途計算する
- lodash の `_.pad(12, 5, '0')` のような非文字列は本体の `pad` では型エラー。`String()` で変換して渡す

## Test

`examples/string-pad.test.ts`
