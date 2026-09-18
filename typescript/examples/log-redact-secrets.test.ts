// カード log-redact-secrets の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

const SECRET_KEYS = ['password', 'token', 'authorization', 'secret', 'apiKey', 'cookie'];

const redact = <T>(value: T, keys: readonly string[] = SECRET_KEYS, mask = '[REDACTED]'): T => {
  const lower = new Set(keys.map((k) => k.toLowerCase()));
  // プレーンオブジェクト（Object.prototype 直下）と null プロトタイプのオブジェクトだけ辿る。
  // Date / Map / クラスインスタンスは中を触らない（契約どおり。呼ぶ前にプレーンにする）
  const isWalkable = (v: object): boolean => {
    const proto = Object.getPrototypeOf(v);
    return proto === Object.prototype || proto === null;
  };
  const walk = (v: unknown): unknown =>
    Array.isArray(v)
      ? v.map(walk)
      : v !== null && typeof v === 'object' && isWalkable(v)
        ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, lower.has(k.toLowerCase()) ? mask : walk(x)]))
        : v;
  return walk(value) as T;
};

describe('log-redact-secrets: redact', () => {
  it('一致したキーの値を [REDACTED] に置き換え、他はそのまま', () => {
    expect(redact({ user: 'a', password: 'p@ss', age: 3 })).toEqual({ user: 'a', password: '[REDACTED]', age: 3 });
  });

  it('キー名は大文字小文字を無視して比較し、部分一致はしない', () => {
    expect(redact({ Authorization: 'Bearer x', TOKEN: 't', apikey: 'k', passwordHash: 'h' })).toEqual({
      Authorization: '[REDACTED]',
      TOKEN: '[REDACTED]',
      apikey: '[REDACTED]',
      passwordHash: 'h',
    });
  });

  it('値は型を問わず丸ごと置き換える（オブジェクト・配列・null も）', () => {
    expect(redact({ token: { a: 1 }, secret: [1, 2], password: null, cookie: undefined })).toEqual({
      token: '[REDACTED]',
      secret: '[REDACTED]',
      password: '[REDACTED]',
      cookie: '[REDACTED]',
    });
  });

  it('ネストしたオブジェクトと配列の中も辿る', () => {
    const input = { headers: { authorization: 'x', accept: 'json' }, items: [{ token: 't', id: 1 }, [{ password: 'p' }]] };
    expect(redact(input)).toEqual({ headers: { authorization: '[REDACTED]', accept: 'json' }, items: [{ token: '[REDACTED]', id: 1 }, [{ password: '[REDACTED]' }]] });
  });

  it('入力を変更せず、プレーンオブジェクトと配列は新しいコピーを返す', () => {
    const input = { password: 'p', nested: { token: 't' }, list: [1] };
    const snapshot = structuredClone(input);
    const output = redact(input);
    expect(input).toEqual(snapshot);
    expect(output).not.toBe(input);
    expect(output.nested).not.toBe(input.nested);
    expect(output.list).not.toBe(input.list);
  });

  it('Date / Map / クラスインスタンス / Error は中を辿らずそのまま返す', () => {
    class Creds {
      password = 'p';
    }
    const date = new Date(0);
    const map = new Map([['password', 'p']]);
    const creds = new Creds();
    const err = new Error('e');
    const out = redact({ date, map, creds, err });
    expect(out.date).toBe(date);
    expect(out.map).toBe(map);
    expect(out.creds).toBe(creds);
    expect(out.creds.password).toBe('p');
    expect(out.err).toBe(err);
  });

  it('keys が空なら何も置き換えず構造だけコピーする。mask は変えられる', () => {
    const input = { password: 'p' };
    const out = redact(input, []);
    expect(out).toEqual(input);
    expect(out).not.toBe(input);
    expect(redact(input, ['password'], '***')).toEqual({ password: '***' });
  });

  it('循環参照はスタックオーバーフローになる', () => {
    const cyc: Record<string, unknown> = { a: 1 };
    cyc.self = cyc;
    expect(() => redact(cyc)).toThrow(RangeError);
  });

  it('Headers はプレーンオブジェクトにしてから渡す', () => {
    const headers = new Headers({ Authorization: 'Bearer x', Accept: 'json' });
    expect(redact(headers)).toBe(headers);
    expect(redact(Object.fromEntries(headers))).toEqual({ authorization: '[REDACTED]', accept: 'json' });
  });
});
