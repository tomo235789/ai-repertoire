// カード date-format-iso の Contract を検証するテスト
import { formatISO } from 'date-fns';
import { describe, expect, it } from 'vitest';

// 実行環境のタイムゾーンから、formatISO が付けるはずのオフセット文字列を組み立てる
function expectedOffset(date: Date): string {
  const offset = date.getTimezoneOffset();
  if (offset === 0) return 'Z';
  const abs = Math.abs(offset);
  const hh = String(Math.trunc(abs / 60)).padStart(2, '0');
  const mm = String(abs % 60).padStart(2, '0');
  return `${offset < 0 ? '+' : '-'}${hh}:${mm}`;
}

describe('date-format-iso: formatISO', () => {
  const d = new Date(2024, 1, 29, 13, 45, 7, 123);

  it('ローカル時刻で整形し、時刻部にはオフセット（0 なら Z）が付く', () => {
    expect(formatISO(d)).toBe(`2024-02-29T13:45:07${expectedOffset(d)}`);
    expect(formatISO(d)).toMatch(/(Z|[+-]\d{2}:\d{2})$/);
  });

  it('ミリ秒は出力せず、年は 4 桁ゼロ埋め', () => {
    expect(formatISO(d)).not.toContain('.123');
    expect(formatISO(new Date(999, 0, 1), { representation: 'date' })).toBe('0999-01-01');
  });

  it("representation で date / time / complete を選べ、date にはオフセットが付かない", () => {
    expect(formatISO(d, { representation: 'date' })).toBe('2024-02-29');
    expect(formatISO(d, { representation: 'time' })).toBe(`13:45:07${expectedOffset(d)}`);
    expect(formatISO(d, { representation: 'complete' })).toBe(formatISO(d));
  });

  it("format: 'basic' で区切りなしになる", () => {
    expect(formatISO(d, { format: 'basic' })).toBe(`20240229T134507${expectedOffset(d)}`);
    expect(formatISO(d, { format: 'basic', representation: 'date' })).toBe('20240229');
  });

  it('無効な Date は RangeError を投げる', () => {
    expect(() => formatISO(new Date(Number.NaN))).toThrow(RangeError);
    expect(() => formatISO(new Date(Number.NaN))).toThrow('Invalid time value');
  });

  it('入力を変更せず、数値や文字列も受け付ける', () => {
    const before = d.getTime();
    formatISO(d);
    expect(d.getTime()).toBe(before);
    expect(formatISO(d.getTime(), { representation: 'date' })).toBe('2024-02-29');
    expect(formatISO('2024-02-29T13:45:07', { representation: 'date' })).toBe('2024-02-29');
  });

  it('同じ入力には同じ結果を返す', () => {
    expect(formatISO(d)).toBe(formatISO(new Date(2024, 1, 29, 13, 45, 7, 123)));
  });
});
