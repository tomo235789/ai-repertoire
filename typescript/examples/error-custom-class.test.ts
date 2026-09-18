// カード error-custom-class の Contract を検証するテスト
import { inspect } from 'node:util';
import { describe, expect, it } from 'vitest';

class HttpError extends Error {
  constructor(
    public readonly status: number,
    message = `HTTP ${status}`,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = 'HttpError';
  }
}

class Unnamed extends Error {}

describe('error-custom-class: class extends Error', () => {
  it('super(message, { cause }) で message と cause が設定され、cause は列挙されない', () => {
    const cause = new Error('row not found');
    const err = new HttpError(404, undefined, { cause });
    expect(err.message).toBe('HTTP 404');
    expect(err.cause).toBe(cause);
    expect(Object.hasOwn(err, 'cause')).toBe(true);
    expect(Object.getOwnPropertyDescriptor(err, 'cause')?.enumerable).toBe(false);
    expect(Object.hasOwn(new HttpError(500), 'cause')).toBe(false); // options を渡さなければプロパティ自体が無い
  });

  it('name は既定で Error のままなので、コンストラクタで代入する', () => {
    expect(new Unnamed('x').name).toBe('Error');
    expect(String(new Unnamed('x'))).toBe('Error: x');
    const err = new HttpError(404);
    expect(err.name).toBe('HttpError');
    expect(String(err)).toBe('HttpError: HTTP 404');
    expect(err.stack?.split('\n')[0]).toBe('HttpError: HTTP 404');
  });

  it('代入した name は列挙可能な自身のプロパティになり、JSON.stringify に現れる。message / stack は現れない', () => {
    const err = new HttpError(404, 'gone', { cause: 'c' });
    expect(Object.keys(err)).toEqual(['status', 'name']);
    expect(JSON.parse(JSON.stringify(err))).toEqual({ status: 404, name: 'HttpError' });
  });

  it('instanceof はプロトタイプ連鎖で判定する（target ES2015 以上）', () => {
    const err = new HttpError(500);
    expect(err).toBeInstanceOf(HttpError);
    expect(err).toBeInstanceOf(Error);
    expect(Object.getPrototypeOf(err)).toBe(HttpError.prototype);
    const caught: unknown = err;
    if (caught instanceof HttpError) expect(caught.status).toBe(500); // 型も絞り込まれる
  });

  it('ES5 相当の壊れ方は setPrototypeOf で直る', () => {
    // ES5 へのダウンレベルでは this のプロトタイプが Error.prototype になる。その状態を再現する
    const broken = Reflect.construct(Error, ['x'], Error) as Error;
    expect(broken instanceof HttpError).toBe(false);
    Object.setPrototypeOf(broken, HttpError.prototype);
    expect(broken instanceof HttpError).toBe(true);
  });

  it('Error.captureStackTrace はファクトリ関数のフレームを stack から隠す。クラス構文のコンストラクタは元々出ない', () => {
    function createPlain() {
      return new HttpError(1);
    }
    function createCaptured() {
      const err = new HttpError(1);
      Error.captureStackTrace?.(err, createCaptured);
      return err;
    }
    function caller() {
      return [createPlain(), createCaptured()];
    }
    const [plain, captured] = caller();
    expect(plain!.stack?.split('\n')[1]).toContain('createPlain'); // コンストラクタ自身のフレーム（new HttpError）は無い
    expect(captured!.stack?.split('\n')[1]).toContain('caller');
    expect(captured!.stack).not.toContain('createCaptured');
  });

  it('util.inspect は stack・列挙可能なプロパティ・[cause] を表示する', () => {
    const shown = inspect(new HttpError(404, 'gone', { cause: new Error('root') }));
    expect(shown).toMatch(/^HttpError: gone\n/);
    expect(shown).toContain('status: 404');
    expect(shown).toContain('[cause]: Error: root');
  });
});
