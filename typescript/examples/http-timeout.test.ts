// カード http-timeout の Contract を検証するテスト
import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import type { AddressInfo } from 'node:net';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

type Route = (req: IncomingMessage, res: ServerResponse) => void;

let server: ReturnType<typeof createServer>;
let base: string;
let routes: Record<string, Route>;
let closedByClient: string[];

beforeEach(async () => {
  routes = {};
  const closed: string[] = []; // 前のテストのサーバーからの close イベントが混ざらないよう、サーバーごとに持つ
  closedByClient = closed;
  server = createServer((req, res) => {
    req.on('close', () => {
      if (!res.writableFinished) closed.push(req.url ?? '');
    });
    (routes[req.url ?? ''] ?? ((_r, res) => res.end('fast')))(req, res);
  });
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

afterEach(async () => {
  server.closeAllConnections(); // 応答を保留したままの接続を切る
  await new Promise<void>((resolve) => server.close(() => resolve()));
});

/** レスポンスを返さないまま保留する */
const hang: Route = () => undefined;

describe('http-timeout: AbortSignal.timeout + fetch', () => {
  it('ms 以内にヘッダーが届かなければ TimeoutError という name の DOMException で reject する', async () => {
    routes['/slow'] = hang;
    const err = await fetch(`${base}/slow`, { signal: AbortSignal.timeout(20) }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(DOMException);
    expect((err as DOMException).name).toBe('TimeoutError');
    expect((err as DOMException).code).toBe(23);
  });

  it('本文の読み取り中も制限時間が効く', async () => {
    routes['/slow-body'] = (_req, res) => {
      res.writeHead(200, { 'content-type': 'text/plain' });
      res.write('part1'); // ヘッダーと先頭だけ送って残りを保留
    };
    const res = await fetch(`${base}/slow-body`, { signal: AbortSignal.timeout(50) });
    expect(res.status).toBe(200);
    const err = await res.text().catch((e: unknown) => e);
    expect((err as DOMException).name).toBe('TimeoutError');
  });

  it('中断されると接続が閉じられ、サーバー側で切断として観測できる', async () => {
    let seen: Promise<void> = Promise.resolve();
    routes['/slow'] = (req) => {
      seen = new Promise((resolve) => req.on('close', () => resolve()));
    };
    await fetch(`${base}/slow`, { signal: AbortSignal.timeout(20) }).catch(() => undefined);
    await seen;
    expect(closedByClient).toEqual(['/slow']);
  });

  it('signal.reason は TimeoutError の DOMException で、fetch はそれをそのまま投げる', async () => {
    routes['/slow'] = hang;
    const signal = AbortSignal.timeout(20);
    const err = await fetch(`${base}/slow`, { signal }).catch((e: unknown) => e);
    expect(signal.aborted).toBe(true);
    expect(signal.reason).toBe(err);
  });

  it('AbortSignal.any で外部キャンセルと併用でき、reason は先に abort した方', async () => {
    routes['/slow'] = hang;
    const controller = new AbortController();
    const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(10_000)]);
    const p = fetch(`${base}/slow`, { signal }).catch((e: unknown) => e);
    controller.abort();
    const err = await p;
    expect((err as DOMException).name).toBe('AbortError');
    expect(signal.reason).toBe(controller.signal.reason);
    const signal2 = AbortSignal.any([new AbortController().signal, AbortSignal.timeout(20)]);
    const err2 = await fetch(`${base}/slow`, { signal: signal2 }).catch((e: unknown) => e);
    expect((err2 as DOMException).name).toBe('TimeoutError');
  });

  it('既に abort 済みの signal なら接続せずに reason で reject する', async () => {
    const err = await fetch(`${base}/fast`, { signal: AbortSignal.abort() }).catch((e: unknown) => e);
    expect((err as DOMException).name).toBe('AbortError');
    expect(closedByClient).toEqual([]);
  });

  it('時間内に終われば通常どおり resolve し、4xx / 5xx でも reject しない', async () => {
    routes['/err'] = (_req, res) => {
      res.writeHead(503);
      res.end();
    };
    const ok = await fetch(`${base}/fast`, { signal: AbortSignal.timeout(10_000) });
    expect(await ok.text()).toBe('fast');
    const bad = await fetch(`${base}/err`, { signal: AbortSignal.timeout(10_000) });
    expect(bad.status).toBe(503);
  });

  it('接続拒否は TypeError で、タイムアウトとは別のエラー', async () => {
    const { port } = server.address() as AddressInfo;
    await new Promise<void>((resolve) => server.close(() => resolve()));
    const err = await fetch(`http://127.0.0.1:${port}/`, { signal: AbortSignal.timeout(10_000) }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(TypeError);
    expect((err as TypeError).message).toBe('fetch failed');
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve)); // afterEach が close できるように
  });
});
