// カード result-try-to-result の Contract を検証するテスト
import { attempt, attemptAsync } from 'es-toolkit';
import { describe, expect, it, vi } from 'vitest';

describe('result-try-to-result: attempt', () => {
  it('正常に返れば [null, 戻り値] を返し、func は 1 回だけ呼ばれる', () => {
    const fn = vi.fn(() => JSON.parse('{"ok":true}') as { ok: boolean });
    expect(attempt(fn)).toEqual([null, { ok: true }]);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('例外を投げれば [投げられた値, null] を返す', () => {
    const [err, value] = attempt(() => JSON.parse('{oops') as unknown);
    expect(err).toBeInstanceOf(SyntaxError);
    expect(value).toBeNull();
  });

  it('Error 以外の値もそのまま返す', () => {
    expect(
      attempt(() => {
        throw 'plain string';
      }),
    ).toEqual(['plain string', null]);
    expect(
      attempt(() => {
        throw undefined;
      }),
    ).toEqual([undefined, null]);
  });

  it('func が undefined を返した場合は [null, undefined]', () => {
    const [err, value] = attempt(() => undefined);
    expect(err).toBeNull();
    expect(value).toBeUndefined();
  });

  it('Promise を返す関数では reject が捕捉されないので attemptAsync を使う', async () => {
    const [err, value] = attempt(() => Promise.reject(new Error('async')));
    expect(err).toBeNull();
    expect(value).toBeInstanceOf(Promise);
    await (value as Promise<never>).catch(() => undefined); // unhandled rejection を防ぐ
    const [err2, value2] = await attemptAsync(() => Promise.reject(new Error('async')));
    expect(err2).toBeInstanceOf(Error);
    expect(value2).toBeNull();
  });

  it('エラー型 E は既定で unknown、明示しても実行時には検証されない', () => {
    const [err] = attempt<never, SyntaxError>(() => {
      throw new TypeError('not syntax');
    });
    expect(err).toBeInstanceOf(TypeError);
    const [err2] = attempt(() => 1);
    const unknownErr: unknown = err2;
    expect(unknownErr).toBeNull();
  });
});
