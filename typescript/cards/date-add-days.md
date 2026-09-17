---
id: date-add-days
lang: typescript
title: 日付に日数を加算する
tags: [日付加算, 日数, 減算, 月末, うるう年, add-days, plus, date-math]
lib: date-fns
fn: addDays
since: "4.0.0"
verified: 2026-09-17
status: public
---

Date に日数を足した新しい Date を返す（負数で減算）。期限日や有効期間の計算に使う。

## Signature

```ts
function addDays<DateType extends Date, ResultDate extends Date = DateType>(date: DateArg<DateType>, amount: number, options?: AddDaysOptions<ResultDate> | undefined): ResultDate
```

## Usage

```ts
import { addDays } from 'date-fns';

const d = new Date(2024, 1, 29); // 2024-02-29 00:00（ローカル）
addDays(d, 1);   // => 2024-03-01 00:00
addDays(d, -1);  // => 2024-02-28 00:00
addDays(d, 366); // => 2025-03-01 00:00
d;               // 変わらない
```

## Contract

- 入力を変更せず、新しい Date を返す（`amount` が 0 でも新しいインスタンス）
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+365 → `2025-02-28`）
- ローカルの日付を進めるので時・分・秒・ミリ秒は保たれる。DST の切替をまたぐと経過時間は 24 時間 × 日数にならない
- 小数の `amount` は「元の日（`getDate()`）+ `amount`」を合算してから **ゼロ方向に切り捨て** る（`setDate` の整数変換）。結果は月内の位置で変わる: 29 日 + `-1.5` → 27 日だが、1 日 + `-1.5` → 0 日 = 前月末日（`Math.floor` でも `Math.trunc` でもない）。日数は整数で渡す
- `amount` が `NaN` / `Infinity`、または入力が無効な Date なら例外を投げず無効な Date を返す
- 数値（epoch ms）や文字列も受け付ける。Date のサブクラスを渡すと同じクラスで返る

## Alternatives

- 週・月・年は `addWeeks` / `addMonths` / `addYears`、まとめて足すなら `add(date, { days: 1, months: 1 })`
- 減算は負数を渡すか `subDays`
- stdlib なら `const r = new Date(d); r.setDate(r.getDate() + n);`
- Temporal なら `Temporal.PlainDate.from('2024-02-29').add({ days: 1 })`

## Pitfalls

- moment の `.add(1, 'days')` は元オブジェクトを書き換えるが、`addDays` は書き換えない。戻り値を使う
- `d.getTime() + n * 86_400_000` の自前計算は DST 切替をまたぐと壁時計の時刻が 1 時間ずれる
- Python の `timedelta(days=1.5)` は 36 時間だが、`addDays(d, 1.5)` は 1 日。時間単位で足すなら `addHours`
- `addMonths` は月末を月の最終日にクランプする（`2024-01-31` + 1 か月 → `2024-02-29`）が、`addDays` にクランプはない

## Test

`examples/date-add-days.test.ts`
