// カード string-pad の Contract を検証するテスト
import { pad } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('string-pad: pad', () => {
  it('左右に詰めて指定長にし、余りが奇数なら右側が 1 文字多い', () => {
    expect(pad('abc', 8)).toBe('  abc   ');
    expect(pad('abc', 7)).toBe('  abc  ');
    expect(pad('abc', 4)).toBe('abc ');
  });

  it('length が元の長さ以下（0・負数・NaN 含む）なら元の文字列を返す', () => {
    expect(pad('abc', 3)).toBe('abc');
    expect(pad('abc', 2)).toBe('abc');
    expect(pad('abc', 0)).toBe('abc');
    expect(pad('abc', -1)).toBe('abc');
    expect(pad('abc', Number.NaN)).toBe('abc');
  });

  it('複数文字の chars は左右それぞれの端から繰り返し、端数は切り落とす', () => {
    expect(pad('abc', 8, '_-')).toBe('_-abc_-_');
    expect(pad('abc', 9, '_-')).toBe('_-_abc_-_');
  });

  it('chars が空文字なら元の文字列を返す', () => {
    expect(pad('abc', 8, '')).toBe('abc');
  });

  it('長さは UTF-16 コード単位で数える（サロゲートペアは 2）', () => {
    const fish = '𩸽';
    expect(fish.length).toBe(2);
    expect(pad(fish, 5, '*')).toBe('*𩸽**');
    expect(pad('あ', 3)).toBe(' あ ');
  });

  it('空文字は chars だけで埋める', () => {
    expect(pad('', 4, '*')).toBe('****');
  });

  it('同じ入力には同じ結果を返し、例外を投げない', () => {
    expect(() => pad('abc', 100, '-')).not.toThrow();
    expect(pad('abc', 6, '-')).toBe(pad('abc', 6, '-'));
  });
});
