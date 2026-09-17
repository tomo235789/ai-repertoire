// カード async-retry の Contract を検証するテスト
import { retry } from 'es-toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

/** n 回失敗してから成功する関数を作る */
const failTimes = (n: number, value = 'ok') => {
  let count = 0;
  return vi.fn(async () => {
    count++;
    if (count <= n) throw new Error(`fail ${count}`);
    return value;
  });
};

describe('async-retry: retry', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('reject したら再実行し、resolve した時点の値を返す', async () => {
    const fn = failTimes(2);
    const p = retry(fn, { retries: 5 });
    await vi.runAllTimersAsync(); // 既定の delay: 0 も setTimeout なので進める
    await expect(p).resolves.toBe('ok');
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it('retries は再試行回数で、合計 retries + 1 回呼ぶ。第 2 引数の数値も retries', async () => {
    const fn = failTimes(10);
    const p = retry(fn, { retries: 2 }).catch((e: unknown) => e);
    await vi.runAllTimersAsync();
    expect(await p).toEqual(new Error('fail 3'));
    expect(fn).toHaveBeenCalledTimes(3);
    const fn2 = failTimes(10);
    const p2 = retry(fn2, 1).catch((e: unknown) => e);
    await vi.runAllTimersAsync();
    expect(await p2).toEqual(new Error('fail 2'));
    expect(fn2).toHaveBeenCalledTimes(2);
  });

  it('省略時は成功するまで無限に試す', async () => {
    const fn = failTimes(50);
    const p = retry(fn);
    await vi.runAllTimersAsync();
    await expect(p).resolves.toBe('ok');
    expect(fn).toHaveBeenCalledTimes(51);
  });

  it('delay の数値分だけ待ってから再実行する', async () => {
    const fn = failTimes(1);
    const p = retry(fn, { retries: 3, delay: 100 });
    await vi.advanceTimersByTimeAsync(99);
    expect(fn).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    await expect(p).resolves.toBe('ok');
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('delay 関数は (attempts, error) を受け取り、attempts は 0 始まり', async () => {
    const seen: [number, string][] = [];
    const fn = failTimes(10);
    const p = retry(fn, {
      retries: 2,
      delay: (attempts, error) => {
        seen.push([attempts, (error as Error).message]);
        return 10;
      },
    });
    const caught = p.catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(100);
    await caught;
    expect(seen).toEqual([
      [0, 'fail 1'],
      [1, 'fail 2'],
    ]);
  });

  it('すべて失敗したら最後のエラーをそのまま投げ、最後の試行のあとは待たない', async () => {
    const errors = [new Error('a'), new Error('b')];
    let i = 0;
    const fn = vi.fn(async () => {
      throw errors[i++];
    });
    const p = retry(fn, { retries: 1, delay: 100 });
    const caught = p.catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(100); // 1 回目の待機のみ
    expect(await caught).toBe(errors[1]);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('shouldRetry が false を返すと即座にそのエラーを投げる', async () => {
    const fn = failTimes(10);
    const shouldRetry = vi.fn((_err: unknown, attempt: number) => attempt < 1);
    const p = retry(fn, { retries: 10, shouldRetry }).catch((e: unknown) => e);
    await vi.runAllTimersAsync();
    expect(await p).toEqual(new Error('fail 2'));
    expect(fn).toHaveBeenCalledTimes(2);
    expect(shouldRetry).toHaveBeenLastCalledWith(expect.any(Error), 1);
  });

  it('開始時点で abort 済みなら func を呼ばずに Error を投げる', async () => {
    const controller = new AbortController();
    controller.abort();
    const fn = failTimes(0);
    await expect(retry(fn, { signal: controller.signal })).rejects.toThrow(/aborted/);
    expect(fn).not.toHaveBeenCalled();
  });

  it('途中で abort されると待機が終わったあと直前のエラーを投げる', async () => {
    const controller = new AbortController();
    const fn = failTimes(10);
    const p = retry(fn, { retries: 10, delay: 100, signal: controller.signal });
    const caught = p.catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(10);
    controller.abort();
    await vi.advanceTimersByTimeAsync(89);
    expect(fn).toHaveBeenCalledTimes(1); // 待機自体は中断されない
    await vi.advanceTimersByTimeAsync(1);
    expect(await caught).toEqual(new Error('fail 1'));
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
