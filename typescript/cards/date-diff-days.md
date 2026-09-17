---
id: date-diff-days
lang: typescript
title: 2 つの日付の暦日差を求める
tags: [日付差, 日数差, 経過日数, 暦日, diff, days-between, difference, calendar-days]
lib: date-fns
fn: differenceInCalendarDays
since: "4.0.0"
verified: 2026-09-17
status: public
---

時刻を無視して、2 つの日付が暦の上で何日離れているかを返す。残り日数の表示や「同じ日か」の判定に使う。

## Signature

```ts
function differenceInCalendarDays(laterDate: DateArg<Date> & {}, earlierDate: DateArg<Date> & {}, options?: DifferenceInCalendarDaysOptions | undefined): number
```

## Usage

```ts
import { differenceInCalendarDays } from 'date-fns';

const later = new Date(2024, 2, 1, 0, 1);      // 2024-03-01 00:01
const earlier = new Date(2024, 1, 29, 23, 59); // 2024-02-29 23:59
differenceInCalendarDays(later, earlier); // => 1（2 分差でも暦日は 1 日違う）
differenceInCalendarDays(earlier, later); // => -1
```

## Contract

- 引数は「後の日付、前の日付」の順。結果は `later - earlier` で、逆順に渡すと負になる
- 時刻を捨てて（ローカルの `startOfDay`）暦日の差を数える。2 分しか離れていなくても日付が変われば 1
- 同じ日なら時刻に関係なく 0
- ローカルタイムゾーンで日付を判定する。DST 切替日（23 時間・25 時間）も 1 日と数える
- 入力を変更しない。数値（epoch ms）や文字列も受け付ける
- どちらかが無効な Date なら `NaN` を返す。例外は投げない

## Alternatives

- 「丸 1 日（ローカルの同時刻まで）が何回あるか」を数えるなら `differenceInDays`（ゼロ方向に切り捨て）
- 週・月・年の暦単位差は `differenceInCalendarWeeks` / `differenceInCalendarMonths` / `differenceInCalendarYears`
- 営業日数は `differenceInBusinessDays`
- 同じ日かだけ知りたいなら `isSameDay`

## Pitfalls

- `differenceInDays` は 24 時間相当の丸 1 日を数えるので、Usage の例は 0 になる。カウントダウン表示は暦日（本関数）、経過日数は丸 1 日、と用途で選ぶ
- moment の `a.diff(b, 'days')` は丸 1 日ベース（`differenceInDays` 相当）
- Python は `(d2.date() - d1.date()).days` が暦日差（本関数と同じ）、`(d2 - d1).days` は 24 時間単位の切り捨て（負のときは −∞ 方向に丸めるので `-1` になりうる）
- `Math.floor((+a - +b) / 86_400_000)` の自前計算は DST 切替をまたぐ 23 時間の日で 0 になる

## Test

`examples/date-diff-days.test.ts`
