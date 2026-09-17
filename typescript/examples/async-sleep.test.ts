// カード async-sleep の Contract を検証するテスト
import { AbortError, delay } from 'es-toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('async-sleep: delay', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('ms 経過後に undefined で resolve する', async () => {
    let done: boolean | undefined;
    const p = delay(100).then((v) => {
      done = v === undefined;
    });
    await vi.advanceTimersByTimeAsync(99);
    expect(done).toBeUndefined();
    await vi.advanceTimersByTimeAsync(1);
    await p;
    expect(done).toBe(true);
  });

  it('signal が abort されると AbortError で reject し、タイマーも止まる', async () => {
    const controller = new AbortController();
    const p = delay(1000, { signal: controller.signal });
    controller.abort();
    await expect(p).rejects.toBeInstanceOf(AbortError);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('既に abort 済みの signal なら即座に reject する', async () => {
    const controller = new AbortController();
    controller.abort();
    await expect(delay(1000, { signal: controller.signal })).rejects.toBeInstanceOf(AbortError);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('AbortError の name は Error なので instanceof で判定する', async () => {
    const controller = new AbortController();
    controller.abort();
    const err = await delay(10, { signal: controller.signal }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(AbortError);
    expect((err as Error).name).toBe('Error');
  });

  it('負の ms は例外にならず最短で resolve する', async () => {
    const p = delay(-5);
    await vi.advanceTimersByTimeAsync(1);
    await expect(p).resolves.toBeUndefined();
  });
});
