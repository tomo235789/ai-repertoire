// カード date-tz-convert の Contract を検証するテスト
import { TZDate, tz } from '@date-fns/tz';
import { addDays, addHours, differenceInHours, format, startOfDay } from 'date-fns';
import { describe, expect, it } from 'vitest';

const utc = new Date('2024-03-10T06:30:00Z'); // 米国の DST 開始日（02:00 → 03:00）

describe('date-tz-convert: TZDate', () => {
  it('Date のサブクラスで、同じ瞬間を指定タイムゾーンの壁時計で読む', () => {
    const tokyo = new TZDate(utc, 'Asia/Tokyo');
    const ny = new TZDate(utc, 'America/New_York');
    expect(tokyo).toBeInstanceOf(Date);
    expect(tokyo.getTime()).toBe(utc.getTime());
    expect(ny.getTime()).toBe(utc.getTime());
    expect([tokyo.getHours(), tokyo.getTimezoneOffset()]).toEqual([15, -540]);
    expect([ny.getHours(), ny.getTimezoneOffset()]).toEqual([1, 300]);
    expect(tokyo.timeZone).toBe('Asia/Tokyo');
  });

  it('toISOString / JSON.stringify はオフセット付き、toString はそのゾーンの表記', () => {
    const tokyo = new TZDate(utc, 'Asia/Tokyo');
    expect(tokyo.toISOString()).toBe('2024-03-10T15:30:00.000+09:00');
    expect(JSON.stringify(tokyo)).toBe('"2024-03-10T15:30:00.000+09:00"');
    expect(new TZDate(utc, 'America/New_York').toString()).toContain('GMT-0500');
    expect(new Date(tokyo).toISOString()).toBe('2024-03-10T06:30:00.000Z'); // UTC に戻す
  });

  it('年月日の引数は指定タイムゾーンの壁時計として解釈する', () => {
    // オフセットを持たない文字列は実行環境のタイムゾーンで解釈されるため、数値引数で指定する
    expect(new TZDate(2024, 0, 1, 0, 'Asia/Tokyo').getTime()).toBe(Date.UTC(2023, 11, 31, 15));
    expect(new TZDate(2024, 0, 1, 9, 'Asia/Tokyo').toISOString()).toBe('2024-01-01T09:00:00.000+09:00');
    // オフセット付きの文字列なら環境に依らない
    expect(new TZDate('2024-01-01T00:00:00Z', 'Asia/Tokyo').toISOString()).toBe('2024-01-01T09:00:00.000+09:00');
  });

  it('date-fns の関数にそのまま渡せ、戻り値も同じゾーンの TZDate。in オプションでも同じ', () => {
    const tokyo = new TZDate(utc, 'Asia/Tokyo');
    expect(format(tokyo, 'yyyy-MM-dd HH:mm xxx')).toBe('2024-03-10 15:30 +09:00');
    const start = startOfDay(tokyo);
    expect(start).toBeInstanceOf(TZDate);
    expect(start.toISOString()).toBe('2024-03-10T00:00:00.000+09:00');
    const viaOption = startOfDay(utc, { in: tz('Asia/Tokyo') });
    expect(viaOption.timeZone).toBe('Asia/Tokyo');
    expect(viaOption.getTime()).toBe(start.getTime());
    expect(format(utc, 'HH:mm xxx', { in: tz('America/New_York') })).toBe('01:30 -05:00');
  });

  it('DST をまたぐ加算: addHours は瞬間ベース、addDays は壁時計の日付を進める', () => {
    const before = new TZDate(2024, 2, 10, 1, 30, 'America/New_York');
    expect(format(before, 'HH:mm xxx')).toBe('01:30 -05:00');
    const plus1h = addHours(before, 1);
    expect(plus1h.toISOString()).toBe('2024-03-10T03:30:00.000-04:00'); // 02:xx は存在しない
    expect(plus1h.getTime() - before.getTime()).toBe(60 * 60 * 1000);
    const noon = new TZDate(2024, 2, 9, 12, 'America/New_York');
    const nextNoon = addDays(noon, 1);
    expect(format(nextNoon, 'yyyy-MM-dd HH:mm xxx')).toBe('2024-03-10 12:00 -04:00');
    expect(differenceInHours(nextNoon, noon)).toBe(23);
  });

  it('存在しない壁時計を setHours で指定すると後ろにずれる', () => {
    const d = new TZDate(2024, 2, 10, 0, 0, 'America/New_York');
    d.setHours(2, 30);
    expect(format(d, 'HH:mm xxx')).toBe('03:30 -04:00');
  });

  it('不正なタイムゾーン名は値の読み出し時に RangeError / NaN になる', () => {
    const bad = new TZDate(utc, 'Not/AZone');
    expect(Number.isNaN(bad.getTime())).toBe(true);
    expect(() => bad.toISOString()).toThrow(RangeError);
    expect(Intl.supportedValuesOf('timeZone')).toContain('Asia/Tokyo');
  });

  it('withTimeZone は同じ瞬間を別のゾーンで読む。Intl は表示だけならこれで足りる', () => {
    const tokyo = new TZDate(utc, 'Asia/Tokyo');
    const london = tokyo.withTimeZone('Europe/London');
    expect(london.getTime()).toBe(tokyo.getTime());
    expect(london.getHours()).toBe(6);
    expect(new Intl.DateTimeFormat('ja-JP', { timeZone: 'Asia/Tokyo', dateStyle: 'short', timeStyle: 'short' }).format(utc)).toBe('2024/03/10 15:30');
  });
});
