// カード function-throttle の Contract を検証するテスト
import { throttle } from 'es-toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('function-throttle: throttle', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('最初は即時実行し、前回の実行から throttleMs 以上経った呼び出しを即時実行する', async () => {
    const calls: number[] = [];
    const t = throttle((n: number) => calls.push(n), 100);
    t(1);
    expect(calls).toEqual([1]);
    await vi.advanceTimersByTimeAsync(50);
    t(2); // 50ms しか経っていないので間引かれる
    expect(calls).toEqual([1]);
    await vi.advanceTimersByTimeAsync(50);
    t(3); // 100ms 経ったので即時
    expect(calls).toEqual([1, 3]);
  });

  it('間引かれた呼び出しは最後の呼び出しから throttleMs 後に最後の引数で末尾実行する', async () => {
    const calls: number[] = [];
    const t = throttle((n: number) => calls.push(n), 100);
    t(1);
    await vi.advanceTimersByTimeAsync(20);
    t(2);
    await vi.advanceTimersByTimeAsync(10);
    t(3); // 最後の呼び出しは 30ms 時点
    await vi.advanceTimersByTimeAsync(99); // 129ms: 区間の終わり(100ms)ではまだ実行されない
    expect(calls).toEqual([1]);
    await vi.advanceTimersByTimeAsync(1); // 130ms = 最後の呼び出し + 100ms
    expect(calls).toEqual([1, 3]);
  });

  it("edges: ['leading'] は末尾実行をしない", async () => {
    const calls: number[] = [];
    const t = throttle((n: number) => calls.push(n), 100, { edges: ['leading'] });
    t(1);
    t(2);
    await vi.advanceTimersByTimeAsync(300);
    expect(calls).toEqual([1]);
  });

  it("edges: ['trailing'] は最初の呼び出しも即時実行せず末尾にまとめる", async () => {
    const calls: number[] = [];
    const t = throttle((n: number) => calls.push(n), 100, { edges: ['trailing'] });
    t(1);
    t(2);
    expect(calls).toEqual([]);
    await vi.advanceTimersByTimeAsync(100);
    expect(calls).toEqual([2]);
  });

  it('cancel は保留中の末尾実行を破棄し、flush は即時実行する', async () => {
    const calls: number[] = [];
    const t = throttle((n: number) => calls.push(n), 100);
    t(1);
    t(2);
    t.cancel();
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toEqual([1]);
    t(3); // 200ms 経過後なので即時
    t(4);
    t.flush();
    expect(calls).toEqual([1, 3, 4]);
  });

  it('signal が abort されると保留中の末尾実行を破棄し、間引き対象の呼び出しは無視される', async () => {
    const fn = vi.fn();
    const controller = new AbortController();
    const t = throttle(fn, 100, { signal: controller.signal });
    t();
    t();
    controller.abort();
    await vi.advanceTimersByTimeAsync(300);
    expect(fn).toHaveBeenCalledTimes(1); // 末尾実行は破棄された
    t(); // 前回の実行から 100ms 以上経っているので abort 後でも即時実行される
    expect(fn).toHaveBeenCalledTimes(2);
    t(); // 100ms 以内の呼び出しは無視され、末尾実行も起きない
    await vi.advanceTimersByTimeAsync(300);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('this を保持し、戻り値は undefined', () => {
    const seen: string[] = [];
    const obj = {
      tag: 'x',
      run: throttle(function (this: { tag: string }) {
        seen.push(this.tag);
        return 42;
      }, 100),
    };
    expect(obj.run()).toBeUndefined();
    expect(seen).toEqual(['x']);
  });
});
