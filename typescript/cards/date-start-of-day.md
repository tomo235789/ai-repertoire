---
id: date-start-of-day
lang: typescript
title: 日付の時刻を 0 時に切り捨てる
tags: [日付の切り捨て, 0時, 日の始まり, 時刻除去, start-of-day, midnight, truncate-time, floor]
lib: date-fns
fn: startOfDay
since: "4.0.0"
verified: 2026-09-17
status: public
---

Date の時刻部分をローカルの 00:00:00.000 にした新しい Date を返す。日単位のキーやグルーピング、範囲検索の下限に使う。

## Signature

```ts
function startOfDay<DateType extends Date, ResultDate extends Date = DateType>(date: DateArg<DateType>, options?: StartOfDayOptions<ResultDate> | undefined): ResultDate
```

## Usage

```ts
import { startOfDay } from 'date-fns';

const d = new Date(2024, 1, 29, 13, 45, 7, 123);
startOfDay(d); // => 2024-02-29 00:00:00.000（ローカル）
d.getHours();  // => 13（元は変わらない）
```

## Contract

- ローカルタイムゾーンの 0 時 0 分 0 秒 0 ミリ秒にする。日付部分は変えない
- 入力を変更せず、新しい Date を返す
- 冪等。`startOfDay(startOfDay(d))` は同じ時刻
- 無効な Date を渡すと無効な Date を返す。例外は投げない
- 数値（epoch ms）や ISO 文字列も受け付ける。`Z` 付き文字列はローカルに換算されてから丸められる
- 結果は実行環境のタイムゾーンに依存する。同じ瞬間でもタイムゾーンが違えば別の epoch ms になる

## Alternatives

- UTC の 0 時にしたいなら `const r = new Date(d); r.setUTCHours(0, 0, 0, 0);`
- 特定のタイムゾーンで丸めるなら `@date-fns/tz` の `tz('Asia/Tokyo')` を `in` オプションに渡す
- 日の終わりは `endOfDay`、週・月は `startOfWeek` / `startOfMonth`
- 同じ日かだけ知りたいなら `isSameDay`

## Pitfalls

- サーバーとブラウザでタイムゾーンが違うと結果が変わる。日付キーを保存するなら UTC か明示的なタイムゾーンで丸める
- `new Date('2024-02-29')` は UTC の 0 時なので、UTC より西のタイムゾーンでは `startOfDay` が前日（2024-02-28）になる
- moment の `.startOf('day')` は元オブジェクトを書き換えるが、`startOfDay` は書き換えない
- Python の `d.replace(hour=0, minute=0, second=0, microsecond=0)` は tzinfo を保ったまま丸める。JS の Date にタイムゾーン情報はなく、常に実行環境のローカルで丸まる

## Test

`examples/date-start-of-day.test.ts`
