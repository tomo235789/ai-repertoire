---
id: date-tz-convert
lang: typescript
title: 日時を別のタイムゾーンで扱う
tags: [タイムゾーン変換, 時差, 別地域の時刻, 夏時間, timezone, tz, TZDate, DST]
lib: "@date-fns/tz"
fn: TZDate
since: "1.0"
verified: 2026-09-17
status: public
---

`new TZDate(date, 'Asia/Tokyo')` で同じ瞬間を指定タイムゾーンの壁時計で読み書きできる `Date` 互換オブジェクトにする。date-fns の関数にそのまま渡せ、実行環境のタイムゾーンに依存しない計算に使う。

## Signature

```ts
class TZDate extends Date { constructor(date: Date | number | string, timeZone: string); constructor(year: number, month: number, ...rest: number[], timeZone: string); readonly timeZone: string; withTimeZone(tz: string): TZDate }
function tz(timeZone: string): (date: Date | number | string) => TZDate  // date-fns の { in } オプションに渡す
```

## Usage

```ts
import { TZDate, tz } from '@date-fns/tz';
import { addHours, format, startOfDay } from 'date-fns';

const utc = new Date('2024-03-10T06:30:00Z');
const tokyo = new TZDate(utc, 'Asia/Tokyo');
format(tokyo, 'yyyy-MM-dd HH:mm xxx');            // => '2024-03-10 15:30 +09:00'（getHours() も 15）
tokyo.getTime() === utc.getTime();                 // => true（同じ瞬間）
startOfDay(utc, { in: tz('Asia/Tokyo') }).toISOString(); // => '2024-03-10T00:00:00.000+09:00'
new TZDate(2024, 2, 10, 1, 30, 'America/New_York');      // 壁時計で指定。3/10 01:30 EST
addHours(new TZDate(2024, 2, 10, 1, 30, 'America/New_York'), 1).toISOString(); // => '2024-03-10T03:30:00.000-04:00'（DST 開始をまたぐ）
```

## Contract

- `TZDate` は `Date` のサブクラス（`instanceof Date` が `true`）。`getTime()` は元の `Date` と同じ瞬間を返し、`getHours()` / `getDate()` / `getTimezoneOffset()` などは **指定タイムゾーンの壁時計** で返す
- `toISOString()` は `Z` ではなく **そのタイムゾーンのオフセット付き**（`2024-03-10T15:30:00.000+09:00`）を返す。`JSON.stringify` も同じ文字列。`toString()` はそのゾーンの表記
- 文字列や年月日の引数は指定タイムゾーンの壁時計として解釈する（`new TZDate('2024-01-01T00:00:00', 'Asia/Tokyo')` は UTC の 2023-12-31T15:00）
- date-fns の関数に渡すと戻り値も同じタイムゾーンの `TZDate` になる。`{ in: tz('...') }` オプションを付けると普通の `Date` を渡しても結果がそのゾーンの `TZDate` になる
- 加算は瞬間ベース。DST 開始日に `addHours(01:30, 1)` は `03:30`（02:00 台は存在しない）、`addDays` は壁時計の日付を進めるので 1 日が 23 時間になる
- 存在しない壁時計（DST の飛んだ時間）を `setHours` で指定すると後ろにずれる（`02:30` → `03:30`）。不正なタイムゾーン名は `RangeError`（`toISOString` などで `Invalid time value`）

## Alternatives

- 表示だけなら `Intl.DateTimeFormat('ja-JP', { timeZone: 'Asia/Tokyo', dateStyle: 'short', timeStyle: 'short' }).format(date)`（依存なし。計算はできない）
- `Temporal.ZonedDateTime`（Node 26 でフラグなしに使える）。新規コードで date-fns を使わないならこちら
- `date-fns-tz` は旧ライブラリ（`toZonedTime` / `fromZonedTime` で `Date` を「ずらす」方式）。新規は `@date-fns/tz`

## Pitfalls

- `TZDate` の `getTime()` は瞬間で `getHours()` は壁時計。「ずらした Date」ではないので、`getTime()` を使う既存コードは変わらず、`getHours()` を使うコードだけ結果が変わる
- `toISOString()` が `Z` で終わらないので、`Z` 前提のパーサーや DB に渡すときは `new Date(tzDate).toISOString()` で UTC に戻す
- `new TZDate(date, tz)` は同じ瞬間を保つが、`new TZDate(year, month, ...)` は壁時計指定。引数の形で意味が変わる
- 実行環境の `TZ` が `Asia/Tokyo` だと `Date` と `TZDate` の区別なく動いてしまい、CI（UTC）で壊れる。テストは別のゾーン（`America/New_York`）で確認する
- タイムゾーン名の妥当性は作成時ではなく値の読み出し時に露見する（`getTime()` が `NaN`）。入力は `Intl.supportedValuesOf('timeZone')` で検証する

## Test

`examples/date-tz-convert.test.ts`
