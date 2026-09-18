// カード http-retry-idempotent の Contract を検証するテスト
import { retry } from 'es-toolkit';
import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { afterEach, describe, expect, it, vi } from 'vitest';

class HttpError extends Error {
  constructor(public status: number) {
    super(`HTTP ${status}`);
    this.name = 'HttpError';
  }
}

/** ステータスの列を順に返す fetch の代替 */
const fetchSequence = (statuses: (number | 'network')[]) =>
  vi.fn(async (_url: string | URL | Request, _init?: RequestInit): Promise<Response> => {
    const next = statuses.shift();
    if (next === 'network') throw new TypeError('fetch failed');
    return new Response(next === 200 ? 'ok' : null, { status: next ?? 200 });
  });

const shouldRetry = (e: unknown) => e instanceof TypeError || (e instanceof HttpError && e.status >= 500);

const fetchIdempotent = (fetchImpl: typeof fetch, url: string, signal?: AbortSignal) =>
  retry(
    async () => {
      const res = await fetchImpl(url, { method: 'GET', signal });
      if (!res.ok) throw new HttpError(res.status);
      return res;
    },
    { retries: 3, delay: 0, shouldRetry, signal },
  );

describe('http-retry-idempotent: retry + fetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetch はステータスに関わらず resolve するので res.ok を見て自分で投げる', async () => {
    const fetchImpl = fetchSequence([500]);
    const res = await fetchImpl('https://example.com/');
    expect(res.ok).toBe(false);
    expect(() => {
      if (!res.ok) throw new HttpError(res.status);
    }).toThrow('HTTP 500');
  });

  it('接続拒否は TypeError（fetch failed）で reject し、原因は cause に入る', async () => {
    const server = createServer();
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
    const { port } = server.address() as AddressInfo;
    await new Promise<void>((resolve) => server.close(() => resolve()));
    const err = await fetch(`http://127.0.0.1:${port}/`).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(TypeError);
    expect((err as TypeError).message).toBe('fetch failed');
    expect((err as TypeError).cause).toBeDefined();
  });

  it('5xx は再試行し、2xx が返った時点でその Response を返す', async () => {
    const fetchImpl = fetchSequence([503, 500, 200]);
    const res = await fetchIdempotent(fetchImpl, 'https://example.com/items/1');
    expect(res.status).toBe(200);
    expect(await res.text()).toBe('ok');
    expect(fetchImpl).toHaveBeenCalledTimes(3);
    expect(fetchImpl).toHaveBeenLastCalledWith('https://example.com/items/1', { method: 'GET', signal: undefined });
  });

  it('ネットワーク断は TypeError で reject し、再試行対象にできる', async () => {
    const fetchImpl = fetchSequence(['network', 200]);
    const res = await fetchIdempotent(fetchImpl, 'https://example.com/');
    expect(res.status).toBe(200);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  it('4xx は shouldRetry が false を返すので 1 回で HttpError を投げる', async () => {
    const fetchImpl = fetchSequence([404, 200]);
    await expect(fetchIdempotent(fetchImpl, 'https://example.com/')).rejects.toMatchObject({ name: 'HttpError', status: 404 });
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it('retries + 1 回すべて 5xx なら最後のエラーを投げる', async () => {
    const fetchImpl = fetchSequence([500, 502, 503, 504, 200]);
    await expect(fetchIdempotent(fetchImpl, 'https://example.com/')).rejects.toMatchObject({ status: 504 });
    expect(fetchImpl).toHaveBeenCalledTimes(4);
  });

  it('signal を abort すると進行中の fetch は AbortError で止まり、次の試行に入らない', async () => {
    const controller = new AbortController();
    const fetchImpl = vi.fn(
      (_url: string | URL | Request, init?: RequestInit) =>
        new Promise<Response>((_, reject) => {
          init?.signal?.addEventListener('abort', () => reject(init.signal!.reason as Error));
        }),
    );
    const p = fetchIdempotent(fetchImpl, 'https://example.com/', controller.signal);
    controller.abort();
    await expect(p).rejects.toMatchObject({ name: 'AbortError' });
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it('グローバル fetch を差し替えても同じ形で使える', async () => {
    const fetchImpl = fetchSequence([500, 200]);
    vi.stubGlobal('fetch', fetchImpl);
    const res = await fetchIdempotent(fetch, 'https://example.com/');
    expect(res.ok).toBe(true);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });
});
