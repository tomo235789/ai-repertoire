// カード log-structured の Contract を検証するテスト
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type Level = 'debug' | 'info' | 'warn' | 'error';

const serializeError = (e: Error): Record<string, unknown> => ({
  name: e.name,
  message: e.message,
  stack: e.stack,
  ...(e.cause instanceof Error && { cause: serializeError(e.cause) }),
});

const RESERVED = ['level', 'time', 'msg'] as const;

const formatLine = (level: Level, msg: string, fields: Record<string, unknown> = {}) => {
  // 予約キーは fields から落とし、メタデータが上書きされないようにする
  const extra = Object.fromEntries(Object.entries(fields).filter(([k]) => !RESERVED.includes(k as (typeof RESERVED)[number])));
  return JSON.stringify({ level, time: new Date().toISOString(), msg, ...extra }, (_k, v: unknown) => (v instanceof Error ? serializeError(v) : v));
};

const log = (level: Level, msg: string, fields?: Record<string, unknown>) => console.log(formatLine(level, msg, fields));

describe('log-structured: console.log + JSON.stringify', () => {
  let out: string[];

  beforeEach(() => {
    out = [];
    vi.spyOn(console, 'log').mockImplementation((...args: unknown[]) => {
      out.push(args.map(String).join(' '));
    });
    vi.useFakeTimers({ now: new Date('2026-09-17T14:00:00.000Z') });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('1 行 1 JSON で、固定キーが先頭、time は UTC の ISO 8601', () => {
    log('info', 'request completed', { method: 'GET', status: 200 });
    expect(out).toHaveLength(1);
    expect(out[0]).toBe('{"level":"info","time":"2026-09-17T14:00:00.000Z","msg":"request completed","method":"GET","status":200}');
    expect(Object.keys(JSON.parse(out[0]!) as object)).toEqual(['level', 'time', 'msg', 'method', 'status']);
  });

  it('msg の改行はエスケープされて行が崩れない', () => {
    log('info', 'line1\nline2');
    expect(out[0]).not.toContain('\n');
    expect((JSON.parse(out[0]!) as { msg: string }).msg).toBe('line1\nline2');
  });

  it('Error はそのままだと {} になるので name / message / stack / cause に展開する', () => {
    const err = new TypeError('boom', { cause: new Error('root') });
    expect(JSON.stringify({ err })).toBe('{"err":{}}');
    log('error', 'request failed', { err });
    const parsed = JSON.parse(out[0]!) as { err: { name: string; message: string; stack: string; cause: { message: string } } };
    expect(parsed.err.name).toBe('TypeError');
    expect(parsed.err.message).toBe('boom');
    expect(parsed.err.stack).toMatch(/^TypeError: boom\n/);
    expect(parsed.err.cause.message).toBe('root');
  });

  it('undefined / 関数 / Symbol は落ち、NaN は null、Date は ISO 文字列、Map / Set は {} になる', () => {
    const line = formatLine('debug', 'x', { a: undefined, f: () => 1, s: Symbol('s'), n: Number.NaN, d: new Date(0), m: new Map([[1, 2]]), set: new Set([1]) });
    expect(JSON.parse(line)).toEqual({ level: 'debug', time: '2026-09-17T14:00:00.000Z', msg: 'x', n: null, d: '1970-01-01T00:00:00.000Z', m: {}, set: {} });
  });

  it('循環参照と BigInt は TypeError でログ自体が失敗する', () => {
    const cyc: Record<string, unknown> = { a: 1 };
    cyc.self = cyc;
    expect(() => log('info', 'x', { cyc })).toThrow(/circular structure/);
    expect(() => log('info', 'x', { big: 1n })).toThrow(/BigInt/);
    expect(out).toHaveLength(0);
  });

  it('fields に予約キー（level / time / msg）があってもメタデータを上書きしない', () => {
    log('info', 'original', { msg: 'override', level: 'warn', userId: 7 });
    expect(JSON.parse(out[0]!)).toMatchObject({ level: 'info', msg: 'original', userId: 7 });
  });

  it('複数引数の console.log は JSON にならない', () => {
    console.log('msg', { level: 'info' });
    expect(() => JSON.parse(out[0]!)).toThrow(SyntaxError);
  });
});
