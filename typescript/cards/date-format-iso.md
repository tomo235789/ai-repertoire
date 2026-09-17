---
id: date-format-iso
lang: typescript
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, date-string, timestamp]
lib: date-fns
fn: formatISO
since: "4.0.0"
verified: 2026-09-17
status: public
---

Date をローカルタイムゾーンの ISO 8601 文字列（`2024-02-29T13:45:07+09:00`）にする。API の送信値やログの日時表記に使う。

## Signature

```ts
function formatISO(date: DateArg<Date> & {}, options?: FormatISOOptions): string
```

## Usage

```ts
import { formatISO } from 'date-fns';

const d = new Date(2024, 1, 29, 13, 45, 7); // ローカル時刻
formatISO(d);                              // => '2024-02-29T13:45:07+09:00'（オフセットは実行環境による）
formatISO(d, { representation: 'date' }); // => '2024-02-29'
formatISO(d, { representation: 'time' }); // => '13:45:07+09:00'
formatISO(d, { format: 'basic' });        // => '20240229T134507+09:00'
```

## Contract

- ローカルタイムゾーンで整形する。時刻部にはそのオフセットが `+09:00` の形で付き、オフセットが 0 のときだけ `Z`
- ミリ秒は出力しない。年は 4 桁ゼロ埋め
- `representation` は `'complete'`（既定）/ `'date'` / `'time'`。`'date'` にはオフセットが付かない
- `format` は `'extended'`（既定、`-` と `:` の区切りあり）/ `'basic'`（区切りなし）
- 無効な Date を渡すと `RangeError`（`Invalid time value`）を投げる
- 入力の Date を変更しない。数値（epoch ms）や文字列も受け付ける
- 純粋関数だが結果は実行環境のタイムゾーンに依存する

## Alternatives

- UTC でよければ stdlib の `date.toISOString()`（常に `Z`、ミリ秒付き）
- 任意の書式は `format(date, 'yyyy-MM-dd')`。ミリ秒を付けたいなら `formatRFC3339(date, { fractionDigits: 3 })`
- 逆変換は `parseISO(str)`

## Pitfalls

- `toISOString()` は UTC に変換するので、UTC より東のタイムゾーンでは日付が前日にずれることがある（JST の `2024-02-29 00:30` は `2024-02-28T15:30:00.000Z`）
- `new Date('2024-02-29')` のような日付のみの文字列は UTC として解釈され、時刻付き（`'2024-02-29T00:00'`）はローカルとして解釈される。ローカルで揃えたいなら `parseISO` を使う
- Python の `datetime.isoformat()` は naive な値にオフセットを付けず、マイクロ秒があれば `.123000` まで出す。`formatISO` は常にオフセット付き・ミリ秒なし

## Test

`examples/date-format-iso.test.ts`
