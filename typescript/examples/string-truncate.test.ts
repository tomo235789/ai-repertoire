// カード string-truncate の Contract を検証するテスト
import { truncate } from 'es-toolkit/compat';
import { describe, expect, it } from 'vitest';

describe('string-truncate: truncate', () => {
  const text = 'The quick brown fox jumps over the lazy dog';

  it('length は省略記号を含めた最大長で、既定は 30 と "..."', () => {
    expect(truncate(text)).toBe('The quick brown fox jumps o...');
    expect(truncate(text)).toHaveLength(30);
    expect(truncate('abcdefghijkl', { length: 10 })).toBe('abcdefg...');
  });

  it('length 以下の文字列は変更しない', () => {
    expect(truncate('abc', { length: 3 })).toBe('abc');
    expect(truncate('abc', { length: 10 })).toBe('abc');
  });

  it('文字列が省略記号以下の長さ、または length が省略記号より短ければ省略記号だけを返す', () => {
    expect(truncate('ABC', { length: 2 })).toBe('...');
    expect(truncate('A', { length: 2 })).toBe('A'); // 切り詰め不要なら省略記号だけにはならない
    expect(truncate('abcdef', { length: 2, omission: '[...]' })).toBe('[...]');
  });

  it('separator を指定すると手前にある最後の区切りで切り、無ければそのまま切る', () => {
    expect(truncate(text, { length: 20, separator: ' ' })).toBe('The quick brown...');
    expect(truncate(text, { length: 20, separator: /,? +/ })).toBe('The quick brown...');
    expect(truncate('abcdefghijkl', { length: 8, separator: ' ' })).toBe('abcde...');
  });

  it('omission を差し替えられる', () => {
    expect(truncate(text, { length: 20, omission: '…' })).toBe('The quick brown fox…');
    expect(truncate('abcdefghijkl', { length: 8, omission: '' })).toBe('abcdefgh');
  });

  it('サロゲートペアを含む文字列はコードポイント単位で数える', () => {
    expect(truncate('¥§✈✉🤓', { length: 5 })).toBe('¥§✈✉🤓');
    expect(truncate('😀😀😀😀😀', { length: 4, omission: '…' })).toBe('😀😀😀…');
    expect(truncate('あいうえおかきくけこ', { length: 6 })).toBe('あいう...');
  });

  it('length が 0 以下なら 0 扱い、undefined は空文字を返し、例外を投げない', () => {
    expect(truncate('ABC', { length: 0 })).toBe('...');
    expect(truncate('ABC', { length: -5 })).toBe('...');
    expect(truncate(undefined)).toBe('');
    expect(truncate('')).toBe('');
  });

  it('同じ入力には同じ結果を返す', () => {
    expect(truncate(text, { length: 12 })).toBe(truncate(text, { length: 12 }));
  });
});
