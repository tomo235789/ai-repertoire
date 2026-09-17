---
id: string-truncate
lang: typescript
title: 長い文字列を省略記号付きで切り詰める
tags: [切り詰め, 省略, 文字数制限, 省略記号, truncate, ellipsis, clip, shorten]
lib: es-toolkit/compat
fn: truncate
since: "1.0.0"
verified: 2026-09-17
status: public
---

文字列が上限を超えるとき、末尾を省略記号に置き換えて上限に収める。一覧表示のタイトルや通知本文の切り詰めに使う。

## Signature

```ts
function truncate(string?: string, options?: TruncateOptions): string
```

## Usage

```ts
import { truncate } from 'es-toolkit/compat';

const text = 'The quick brown fox jumps over the lazy dog';
truncate(text);                                // => 'The quick brown fox jumps o...'
truncate(text, { length: 20, separator: ' ' }); // => 'The quick brown...'
truncate(text, { length: 20, omission: '…' });  // => 'The quick brown fox…'
```

## Contract

- `length`（既定 30）は **省略記号を含めた** 結果の最大長。結果は先頭 `length - omission.length` 文字 + `omission`
- 文字列の長さが `length` 以下なら変更せずに返す
- 切り詰めが必要（文字列の長さが `length` より大きい）なとき、文字列の長さが `omission`（既定 `'...'`）の長さ以下、または `length` が `omission` より短いなら `omission` だけを返す。この場合、結果は `length` を超えうる（`truncate('A', { length: 2 })` は切り詰め不要なので `'A'`）
- `separator`（文字列または RegExp）を指定すると、切り詰め位置より手前にある最後の `separator` の直前で切る。見つからなければ `separator` 無しと同じ
- サロゲートペアや結合文字を含む文字列はコードポイント単位で数え、含まなければ UTF-16 コード単位で数える
- `length` が 0 以下なら 0 扱い。`string` が `undefined` なら `''` を返す。例外を投げない
- 純粋関数

## Alternatives

- 省略記号なしで単に切るなら `str.slice(0, n)`。書記素単位で切るなら `Intl.Segmenter`
- 表示上だけ省略するなら CSS の `text-overflow: ellipsis`
- es-toolkit 本体には `truncate` が無い。`es-toolkit/compat` から import する

## Pitfalls

- `length` に省略記号の分が含まれる。「本文 n 文字 + 省略記号」にしたければ `length: n + omission.length`
- `omission` が `length` より長いと結果は `length` を超える（`truncate('abcdef', { length: 2, omission: '[...]' })` → `'[...]'`）
- 家族絵文字のような ZWJ 結合列はコードポイント単位で分断されうる。書記素単位で切りたければ `Intl.Segmenter` で分割してから結合する
- Python の `textwrap.shorten` は連続空白を 1 つにまとめ、常に単語境界で切る（既定の省略記号は `' [...]'`）。`truncate` は `separator` を渡さない限り文字位置で切る

## Test

`examples/string-truncate.test.ts`
