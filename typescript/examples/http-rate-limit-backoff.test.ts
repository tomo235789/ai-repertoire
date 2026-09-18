// カード http-rate-limit-backoff の Contract を検証するテスト
import { retry } from 'es-toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

class RateLimited extends Error {
  constructor(
    public status: number,
    public retryAfterMs: number | null,
  ) {
    super(`HTTP ${status}`);
    this.name = 'RateLimited';
  }
}

/** Retry-After ヘッダーをミリ秒にする。秒数か HTTP 日付、無ければ null */
const retryAfterMs = (value: string | null): number | null => {
  if (value === null) return null;
  const trimmed = value.trim();
  if (/^\d+$/.test(trimmed)) {
    // 秒数は十進の非負整数だけ受ける（指数表記・負数・Infinity は弾く）
    const ms = Number(trimmed) * 1000;
    return Number.isSafeInteger(ms) ? ms : null;
  }
  const at = Date.parse(trimmed);
  return Number.isNaN(at) ? null : Math.max(0, at - Date.now());
};

const backoff = (attempt: number, e: unknown, jitter = 0) => {
  const hinted = (e as RateLimited).retryAfterMs;
  return hinted !== null ? hinted : Math.min(500 * 2 ** attempt, 30_000) + jitter;
};

/** ステータス（とヘッダー）の列を順に返す fetch の代替 */
const fetchSequence = (responses: (number | [number, Record<string, string>])[]) =>
  vi.fn(async (): Promise<Response> => {
    const next = responses.shift() ?? 200;
    const [status, headers] = Array.isArray(next) ? next : [next, {}];
    return new Response(status === 200 ? 'ok' : null, { status, headers });
  });

const fetchWithBackoff = (fetchImpl: () => Promise<Response>, delays: number[]) =>
  retry(
    async () => {
      const res = await fetchImpl();
      if (res.status === 429 || res.status === 503) throw new RateLimited(res.status, retryAfterMs(res.headers.get('retry-after')));
      return res;
    },
    {
      retries: 5,
      shouldRetry: (e) => e instanceof RateLimited,
      delay: (attempt, e) => {
        const ms = backoff(attempt, e);
        delays.push(ms);
        return ms;
      },
    },
  );

describe('http-rate-limit-backoff: retry + Retry-After', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('429 / 503 は指数バックオフで待って再試行し、attempts は 0 始まり', async () => {
    const fetchImpl = fetchSequence([429, 503, 429, 200]);
    const delays: number[] = [];
    const p = fetchWithBackoff(fetchImpl, delays);
    await vi.runAllTimersAsync();
    expect((await p).status).toBe(200);
    expect(delays).toEqual([500, 1000, 2000]);
    expect(fetchImpl).toHaveBeenCalledTimes(4);
  });

  it('delay が返したミリ秒だけ待ってから次の試行に入る', async () => {
    const fetchImpl = fetchSequence([429, 200]);
    const p = fetchWithBackoff(fetchImpl, []);
    await vi.advanceTimersByTimeAsync(499);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
    await expect(p).resolves.toBeInstanceOf(Response);
  });

  it('Retry-After（秒）があればそちらを優先する', async () => {
    const fetchImpl = fetchSequence([[429, { 'Retry-After': '3' }], 200]);
    const delays: number[] = [];
    const p = fetchWithBackoff(fetchImpl, delays);
    await vi.runAllTimersAsync();
    await p;
    expect(delays).toEqual([3000]);
  });

  it('Retry-After が HTTP 日付なら Number は NaN になるので Date.parse にフォールバックする', () => {
    vi.setSystemTime(new Date('2015-10-21T07:27:58Z'));
    expect(Number('Wed, 21 Oct 2015 07:28:00 GMT')).toBeNaN();
    expect(retryAfterMs('Wed, 21 Oct 2015 07:28:00 GMT')).toBe(2000);
    expect(retryAfterMs('3')).toBe(3000);
    expect(retryAfterMs(null)).toBeNull();
    expect(retryAfterMs('soon')).toBeNull();
    expect(new Response(null, { headers: { 'Retry-After': '2' } }).headers.get('retry-after')).toBe('2'); // 大文字小文字を区別しない
  });

  it('shouldRetry で 429 / 503 に限定するので 500 や 404 は再試行しない', async () => {
    const fetchImpl = fetchSequence([500, 200]);
    const res = await fetchWithBackoff(fetchImpl, []);
    expect(res.status).toBe(500); // 対象外はそのまま返る（別の判定はカード http-retry-idempotent）
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it('retries 回すべて失敗したら最後のエラーを投げ、最後の試行のあとは待たない', async () => {
    const fetchImpl = fetchSequence([429, 429, 429, 429, 429, 503]);
    const delays: number[] = [];
    const caught = fetchWithBackoff(fetchImpl, delays).catch((e: unknown) => e);
    await vi.runAllTimersAsync();
    expect(await caught).toMatchObject({ name: 'RateLimited', status: 503 });
    expect(fetchImpl).toHaveBeenCalledTimes(6);
    expect(delays).toEqual([500, 1000, 2000, 4000, 8000]);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('上限 cap で頭打ちになり、ジッターは加算される', () => {
    const e = new RateLimited(429, null);
    expect(backoff(10, e)).toBe(30_000);
    expect(backoff(0, e, 123)).toBe(623);
    vi.spyOn(Math, 'random').mockReturnValue(0.5);
    expect(backoff(1, e, Math.random() * 500)).toBe(1250);
  });
});
