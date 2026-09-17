// カード date-start-of-day の Contract を検証するテスト
import { startOfDay } from 'date-fns';
import { describe, expect, it } from 'vitest';

describe('date-start-of-day: startOfDay', () => {
  const d = new Date(2024, 1, 29, 13, 45, 7, 123);

  it('ローカルの 00:00:00.000 にし、日付は変えない', () => {
    const result = startOfDay(d);
    expect(result).toEqual(new Date(2024, 1, 29));
    expect([result.getHours(), result.getMinutes(), result.getSeconds(), result.getMilliseconds()]).toEqual([0, 0, 0, 0]);
    expect([result.getFullYear(), result.getMonth(), result.getDate()]).toEqual([2024, 1, 29]);
  });

  it('入力を変更せず新しい Date を返す', () => {
    const result = startOfDay(d);
    expect(result).not.toBe(d);
    expect(d).toEqual(new Date(2024, 1, 29, 13, 45, 7, 123));
  });

  it('冪等', () => {
    const once = startOfDay(d);
    expect(startOfDay(once).getTime()).toBe(once.getTime());
  });

  it('無効な Date は無効な Date を返し、例外を投げない', () => {
    expect(Number.isNaN(startOfDay(new Date(Number.NaN)).getTime())).toBe(true);
  });

  it('数値や ISO 文字列も受け付け、Z 付き文字列はローカルに換算してから丸める', () => {
    expect(startOfDay(d.getTime())).toEqual(new Date(2024, 1, 29));
    expect(startOfDay('2024-02-29T23:59:59')).toEqual(new Date(2024, 1, 29));
    const utc = '2024-02-29T23:59:59Z';
    expect(startOfDay(utc)).toEqual(startOfDay(new Date(utc)));
  });

  it('結果は実行環境のタイムゾーンに依存する（ローカルのオフセット分だけ UTC の 0 時とずれる）', () => {
    const result = startOfDay(d);
    const utcMidnight = Date.UTC(2024, 1, 29);
    expect(result.getTime() - utcMidnight).toBe(result.getTimezoneOffset() * 60_000);
  });
});
