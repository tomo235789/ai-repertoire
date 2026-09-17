// カード number-mean の Contract を検証するテスト
import { mean } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('number-mean: mean', () => {
  it('算術平均を返し、入力を変更しない', () => {
    const nums = [1, 2, 3, 4, 5];
    expect(mean(nums)).toBe(3);
    expect(mean([1, 2])).toBe(1.5);
    expect(nums).toEqual([1, 2, 3, 4, 5]);
  });

  it('空配列は例外ではなく NaN を返す', () => {
    expect(() => mean([])).not.toThrow();
    expect(mean([])).toBeNaN();
  });

  it('NaN を含む、または Infinity と -Infinity を両方含むと NaN', () => {
    expect(mean([1, Number.NaN])).toBeNaN();
    expect(mean([Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY])).toBeNaN();
  });

  it('型変換をしないので undefined を含むと NaN', () => {
    expect(mean([1, undefined, 3] as unknown as number[])).toBeNaN();
    expect(mean(new Array<number>(2))).toBeNaN();
  });

  it('浮動小数点の誤差はそのまま', () => {
    expect(mean([0.1, 0.2, 0.3])).toBe(0.20000000000000004);
  });
});
