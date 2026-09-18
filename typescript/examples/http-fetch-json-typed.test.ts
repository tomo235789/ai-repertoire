// カード http-fetch-json-typed の Contract を検証するテスト
import { afterEach, describe, expect, it, vi } from 'vitest';
import { z } from 'zod';

const User = z.object({ id: z.number(), name: z.string() });
type User = z.infer<typeof User>;

const fetchUser = async (url: string): Promise<User> => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return User.parse(await res.json());
};

/** 次の fetch が返す Response を決める */
const respondWith = (body: string | null, init?: ResponseInit) =>
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(body, init)),
  );

describe('http-fetch-json-typed: zod parse', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('res.ok を確認し、JSON をスキーマの型で返す', async () => {
    respondWith('{"id":1,"name":"a"}', { headers: { 'content-type': 'application/json' } });
    const user = await fetchUser('https://example.com/users/1');
    expect(user).toEqual({ id: 1, name: 'a' });
  });

  it('fetch は 4xx / 5xx でも resolve するので res.ok で分岐する', async () => {
    respondWith('{"error":"not found"}', { status: 404 });
    await expect(fetchUser('https://example.com/users/9')).rejects.toThrow('HTTP 404');
    const res = await fetch('https://example.com/users/9');
    expect(res.ok).toBe(false);
    expect(await res.json()).toEqual({ error: 'not found' }); // 本文自体は JSON として読める
  });

  it('res.json() は Content-Type を見ない。本文が JSON でなければ SyntaxError', async () => {
    respondWith('<html>', { headers: { 'content-type': 'application/json' } });
    await expect(fetchUser('https://example.com/')).rejects.toThrow(SyntaxError);
    respondWith('{"id":2,"name":"b"}', { headers: { 'content-type': 'text/plain' } });
    expect(await fetchUser('https://example.com/')).toEqual({ id: 2, name: 'b' });
    respondWith('');
    await expect(fetchUser('https://example.com/')).rejects.toThrow('Unexpected end of JSON input');
  });

  it('parse は未定義キーを取り除いた新しいオブジェクトを返し、元の値は変更しない', () => {
    const raw = { id: 1, name: 'a', extra: true };
    const parsed = User.parse(raw);
    expect(parsed).toEqual({ id: 1, name: 'a' });
    expect(parsed).not.toBe(raw);
    expect(raw).toEqual({ id: 1, name: 'a', extra: true });
  });

  it('形が違えば ZodError を投げ、issues に path / code / message が入る', async () => {
    respondWith('{"id":"1","name":"a"}');
    const err = await fetchUser('https://example.com/').catch((e: unknown) => e);
    expect(err).toBeInstanceOf(z.ZodError);
    expect(err).toBeInstanceOf(Error);
    expect((err as z.ZodError).name).toBe('ZodError');
    expect((err as z.ZodError).issues).toMatchObject([{ path: ['id'], code: 'invalid_type' }]);
    expect(z.prettifyError(err as z.ZodError)).toContain('at id');
  });

  it('safeParse は例外ではなく success で結果を返す', () => {
    expect(User.safeParse({ id: 1, name: 'a' })).toEqual({ success: true, data: { id: 1, name: 'a' } });
    const failed = User.safeParse({ id: 'x' });
    expect(failed.success).toBe(false);
    expect(failed.error).toBeInstanceOf(z.ZodError);
  });

  it('本文は 1 回しか読めない', async () => {
    const res = new Response('{}');
    await res.json();
    await expect(res.text()).rejects.toThrow(TypeError);
  });

  it('strict は未定義キーをエラーにし、loose は残す', () => {
    expect(User.strict().safeParse({ id: 1, name: 'a', extra: 1 }).success).toBe(false);
    expect(User.loose().parse({ id: 1, name: 'a', extra: 1 })).toEqual({ id: 1, name: 'a', extra: 1 });
  });

  it('z.number() は文字列を受け付けないので、数値が文字列で返る API は z.coerce.number()', () => {
    expect(z.number().safeParse('1').success).toBe(false);
    expect(z.coerce.number().parse('1')).toBe(1);
  });
});
