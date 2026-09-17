// カード function-pipe の Contract を検証するテスト
import { flow, flowRight } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('function-pipe: flow', () => {
  it('最初の関数は全引数を受け取り、以降は直前の戻り値を左から順に受け取る', () => {
    const order: string[] = [];
    const add = (a: number, b: number) => {
      order.push('add');
      return a + b;
    };
    const double = (n: number) => {
      order.push('double');
      return n * 2;
    };
    const toLabel = (n: number) => `total: ${n}`;
    expect(flow(add, double, toLabel)(1, 2)).toBe('total: 6');
    expect(order).toEqual(['add', 'double']);
  });

  it('関数 0 個なら第 1 引数をそのまま返す', () => {
    expect(flow()(7, 8)).toBe(7);
  });

  it('5 個までは型が推論される', () => {
    const f = flow(
      (s: string) => s.length,
      (n) => n + 1,
      (n) => n * 2,
      (n) => String(n),
      (s) => s.padStart(4, '0'),
    );
    const result: string = f('abc');
    expect(result).toBe('0008');
  });

  it('this をすべての関数に渡す', () => {
    const obj = {
      base: 10,
      run: flow(
        function (this: { base: number }, n: number) {
          return this.base + n;
        },
        function (this: { base: number }, n: number) {
          return this.base * n;
        },
      ),
    };
    expect(obj.run(1)).toBe(110);
  });

  it('非同期関数を混ぜても await せず Promise がそのまま次に渡る', async () => {
    const received: unknown[] = [];
    const f = flow(
      async (n: number) => n + 1,
      (p) => {
        received.push(p);
        return p;
      },
    );
    const result = f(1);
    expect(received[0]).toBeInstanceOf(Promise);
    expect(await result).toBe(2);
  });

  it('flowRight は右から左に合成する', () => {
    const toLabel = (n: number) => `total: ${n}`;
    const double = (n: number) => n * 2;
    const add = (a: number, b: number) => a + b;
    expect(flowRight(toLabel, double, add)(1, 2)).toBe('total: 6');
  });

  it('渡した関数を変更せず、合成結果は新しい関数', () => {
    const inc = (n: number) => n + 1;
    const f = flow(inc);
    expect(f).not.toBe(inc);
    expect(inc(1)).toBe(2);
  });
});
