// カード function-debounce の Contract を検証するテスト
import { debounce } from 'es-toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('function-debounce: debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('既定では最後の呼び出しから debounceMs 後に最後の引数で 1 回だけ実行する', async () => {
    const calls: string[] = [];
    const d = debounce((s: string) => calls.push(s), 100);
    d('a');
    await vi.advanceTimersByTimeAsync(50);
    d('ab');
    await vi.advanceTimersByTimeAsync(50);
    d('abc');
    await vi.advanceTimersByTimeAsync(99);
    expect(calls).toEqual([]); // 途中の呼び出しでタイマーが張り直される
    await vi.advanceTimersByTimeAsync(1);
    expect(calls).toEqual(['abc']);
  });

  it("edges: ['leading'] は最初を即時実行し、以後の呼び出しは捨てる", async () => {
    const calls: number[] = [];
    const d = debounce((n: number) => calls.push(n), 100, { edges: ['leading'] });
    d(1);
    expect(calls).toEqual([1]);
    d(2);
    d(3);
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toEqual([1]);
  });

  it("edges: ['leading', 'trailing'] は 2 回以上呼ばれたときだけ末尾でも実行する", async () => {
    const calls: number[] = [];
    const d = debounce((n: number) => calls.push(n), 100, { edges: ['leading', 'trailing'] });
    d(1);
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toEqual([1]); // 1 回だけなら末尾は実行されない
    d(2);
    d(3);
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toEqual([1, 2, 3]);
  });

  it('cancel は保留中の実行を破棄する', async () => {
    const fn = vi.fn();
    const d = debounce(fn, 100);
    d();
    d.cancel();
    await vi.advanceTimersByTimeAsync(200);
    expect(fn).not.toHaveBeenCalled();
  });

  it('flush は保留中の呼び出しがあればその場で実行し、無ければ何もしない', async () => {
    const calls: number[] = [];
    const d = debounce((n: number) => calls.push(n), 100);
    d.flush();
    expect(calls).toEqual([]);
    d(1);
    d.flush();
    expect(calls).toEqual([1]);
    d.flush();
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toEqual([1]); // 二重実行しない
  });

  it('schedule はタイマーだけを張り直す', async () => {
    const calls: number[] = [];
    const d = debounce((n: number) => calls.push(n), 100);
    d(1);
    await vi.advanceTimersByTimeAsync(60);
    d.schedule();
    await vi.advanceTimersByTimeAsync(60);
    expect(calls).toEqual([]);
    await vi.advanceTimersByTimeAsync(40);
    expect(calls).toEqual([1]);
  });

  it('signal が abort されると保留を破棄し、以後の呼び出しを無視する', async () => {
    const fn = vi.fn();
    const controller = new AbortController();
    const d = debounce(fn, 100, { signal: controller.signal });
    d();
    controller.abort();
    await vi.advanceTimersByTimeAsync(200);
    expect(fn).not.toHaveBeenCalled();
    d();
    await vi.advanceTimersByTimeAsync(200);
    expect(fn).not.toHaveBeenCalled();
  });

  it('this を保持し、戻り値は undefined', async () => {
    const seen: unknown[] = [];
    const obj = {
      tag: 'x',
      run: debounce(function (this: { tag: string }) {
        seen.push(this.tag);
        return 42;
      }, 100),
    };
    const result = obj.run();
    expect(result).toBeUndefined();
    await vi.advanceTimersByTimeAsync(100);
    expect(seen).toEqual(['x']);
  });

  it('状態は debounce した関数ごとに独立し、元の関数は変更されない', async () => {
    const fn = vi.fn();
    const d1 = debounce(fn, 100);
    const d2 = debounce(fn, 100);
    d1();
    d2();
    d1.cancel();
    await vi.advanceTimersByTimeAsync(100);
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn()).toBeUndefined(); // fn は直接呼べる
  });
});
