// カード async-timeout の Contract を検証するテスト
import { TimeoutError, withTimeout } from 'es-toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const resolveAfter = <T>(ms: number, value: T) => new Promise<T>((resolve) => setTimeout(() => resolve(value), ms));

describe('async-timeout: withTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('run は同期的に 1 回呼ばれ、ms 以内に resolve すればその値を返す', async () => {
    const run = vi.fn(() => resolveAfter(50, 'ok'));
    const p = withTimeout(run, 100);
    expect(run).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(50);
    await expect(p).resolves.toBe('ok');
  });

  it('ms 以内に決着しなければ TimeoutError で reject する', async () => {
    const p = withTimeout(() => resolveAfter(200, 'late'), 100);
    const caught = p.catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(100);
    const err = await caught;
    expect(err).toBeInstanceOf(TimeoutError);
    expect(err).toBeInstanceOf(DOMException);
    expect((err as Error).name).toBe('Error'); // name では判定できない
  });

  it('タイムアウトしても元の Promise は止まらない', async () => {
    let finished = false;
    const original = resolveAfter(200, 'late').then(() => {
      finished = true;
    });
    const caught = withTimeout(() => original, 100).catch((e: unknown) => e);
    await vi.advanceTimersByTimeAsync(100);
    expect(await caught).toBeInstanceOf(TimeoutError);
    expect(finished).toBe(false);
    await vi.advanceTimersByTimeAsync(100);
    expect(finished).toBe(true);
  });

  it('run が reject した場合はそのエラーがそのまま伝わる', async () => {
    const boom = new Error('boom');
    await expect(withTimeout(() => Promise.reject(boom), 100)).rejects.toBe(boom);
  });

  it('signal が abort されるとタイムアウトだけが止まり、run の決着を待つ', async () => {
    const controller = new AbortController();
    const p = withTimeout(() => resolveAfter(200, 'late'), 100, { signal: controller.signal });
    controller.abort();
    await vi.advanceTimersByTimeAsync(200);
    await expect(p).resolves.toBe('late');
  });

  it('既に abort 済みの signal ならタイムアウトは働かない', async () => {
    const controller = new AbortController();
    controller.abort();
    const p = withTimeout(() => resolveAfter(200, 'late'), 100, { signal: controller.signal });
    await vi.advanceTimersByTimeAsync(200);
    await expect(p).resolves.toBe('late');
  });

  it('run が先に決着してもタイムアウト用のタイマーは残る', async () => {
    await withTimeout(() => Promise.resolve('fast'), 100);
    expect(vi.getTimerCount()).toBe(1);
    await vi.advanceTimersByTimeAsync(100);
    expect(vi.getTimerCount()).toBe(0);
  });
});
