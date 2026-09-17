// カード date-diff-days の Contract を検証するテスト
import { differenceInCalendarDays, differenceInDays } from 'date-fns';
import { describe, expect, it } from 'vitest';

describe('date-diff-days: differenceInCalendarDays', () => {
  const later = new Date(2024, 2, 1, 0, 1);
  const earlier = new Date(2024, 1, 29, 23, 59);

  it('引数は「後、前」の順で、逆順なら負になる', () => {
    expect(differenceInCalendarDays(later, earlier)).toBe(1);
    expect(differenceInCalendarDays(earlier, later)).toBe(-1);
    expect(differenceInCalendarDays(new Date(2025, 1, 28), new Date(2024, 1, 28))).toBe(366);
  });

  it('時刻を捨てて暦日の差を数える（differenceInDays は丸 1 日を数える）', () => {
    expect(differenceInCalendarDays(later, earlier)).toBe(1);
    expect(differenceInDays(later, earlier)).toBe(0);
  });

  it('同じ日なら時刻に関係なく 0', () => {
    expect(differenceInCalendarDays(new Date(2024, 1, 29, 23, 59), new Date(2024, 1, 29, 0, 0))).toBe(0);
    expect(differenceInCalendarDays(new Date(2024, 1, 29, 0, 0), new Date(2024, 1, 29, 23, 59))).toBe(0);
  });

  it('ローカルタイムゾーンの日付で判定する', () => {
    // ローカルで 23:59 と翌日 00:00 は epoch では 1 分差だが、暦日は 1 日違う
    const a = new Date(2024, 1, 29, 23, 59);
    const b = new Date(a.getTime() + 60_000);
    expect(b.getDate()).toBe(1);
    expect(differenceInCalendarDays(b, a)).toBe(1);
  });

  it('入力を変更せず、数値や文字列も受け付ける', () => {
    const a = new Date(2024, 2, 1, 5);
    const b = new Date(2024, 1, 29, 5);
    differenceInCalendarDays(a, b);
    expect(a).toEqual(new Date(2024, 2, 1, 5));
    expect(b).toEqual(new Date(2024, 1, 29, 5));
    expect(differenceInCalendarDays(a.getTime(), b.getTime())).toBe(1);
    expect(differenceInCalendarDays('2024-03-01T05:00:00', '2024-02-29T05:00:00')).toBe(1);
  });

  it('無効な Date を含むと NaN を返し、例外を投げない', () => {
    expect(differenceInCalendarDays(new Date(Number.NaN), earlier)).toBeNaN();
    expect(differenceInCalendarDays(later, new Date(Number.NaN))).toBeNaN();
  });
});
