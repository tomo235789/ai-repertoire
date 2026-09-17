// カード date-add-days の Contract を検証するテスト
import { addDays } from 'date-fns';
import { describe, expect, it } from 'vitest';

describe('date-add-days: addDays', () => {
  it('入力を変更せず新しい Date を返す（amount が 0 でも別インスタンス）', () => {
    const d = new Date(2024, 1, 29);
    const result = addDays(d, 1);
    expect(d).toEqual(new Date(2024, 1, 29));
    expect(result).not.toBe(d);
    expect(addDays(d, 0)).not.toBe(d);
    expect(addDays(d, 0)).toEqual(d);
  });

  it('月末・年末・うるう年をカレンダーどおりに繰り越す', () => {
    expect(addDays(new Date(2024, 1, 29), 1)).toEqual(new Date(2024, 2, 1));
    expect(addDays(new Date(2024, 1, 29), -1)).toEqual(new Date(2024, 1, 28));
    expect(addDays(new Date(2024, 1, 29), 365)).toEqual(new Date(2025, 1, 28));
    expect(addDays(new Date(2024, 1, 29), 366)).toEqual(new Date(2025, 2, 1));
    expect(addDays(new Date(2023, 2, 1), -1)).toEqual(new Date(2023, 1, 28));
    expect(addDays(new Date(2024, 11, 31), 1)).toEqual(new Date(2025, 0, 1));
  });

  it('ローカルの日付を進めるので時・分・秒・ミリ秒は保たれる', () => {
    const d = new Date(2024, 1, 29, 13, 45, 7, 123);
    expect(addDays(d, 1)).toEqual(new Date(2024, 2, 1, 13, 45, 7, 123));
  });

  it('小数の amount は「日 + amount」をゼロ方向に切り捨てる（月内の位置で結果が変わる）', () => {
    const d = new Date(2024, 1, 29);
    expect(addDays(d, 1.5)).toEqual(new Date(2024, 2, 1)); // 29 + 1.5 = 30.5 → 30 日 = 3/1
    expect(addDays(d, -1.5)).toEqual(new Date(2024, 1, 27)); // 29 - 1.5 = 27.5 → 27 日
    const first = new Date(2024, 2, 1);
    expect(addDays(first, -1.5)).toEqual(new Date(2024, 1, 29)); // 1 - 1.5 = -0.5 → 0 日 = 前月末（floor なら 2/28）
    expect(addDays(first, -0.5)).toEqual(new Date(2024, 1, 29)); // 1 - 0.5 = 0.5 → 0 日 = 前月末
  });

  it('NaN / Infinity や無効な Date では例外を投げず無効な Date を返す', () => {
    const d = new Date(2024, 1, 29);
    expect(Number.isNaN(addDays(d, Number.NaN).getTime())).toBe(true);
    expect(Number.isNaN(addDays(d, Number.POSITIVE_INFINITY).getTime())).toBe(true);
    expect(Number.isNaN(addDays(new Date(Number.NaN), 1).getTime())).toBe(true);
  });

  it('数値や文字列も受け付け、Date のサブクラスは同じクラスで返る', () => {
    const d = new Date(2024, 1, 29);
    expect(addDays(d.getTime(), 1)).toEqual(new Date(2024, 2, 1));
    expect(addDays('2024-02-29T00:00:00', 1)).toEqual(new Date(2024, 2, 1));
    class MyDate extends Date {}
    expect(addDays(new MyDate(2024, 1, 29), 1)).toBeInstanceOf(MyDate);
  });
});
