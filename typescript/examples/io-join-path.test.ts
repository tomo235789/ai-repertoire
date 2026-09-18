// カード io-join-path の Contract を検証するテスト
import { join, posix, resolve, sep, win32 } from 'node:path';
import { describe, expect, it } from 'vitest';

describe('io-join-path: path.join', () => {
  it('.. と . と重複した区切りを正規化し、空文字列は無視する', () => {
    expect(posix.join('logs', 'app', '../db', 'x.sqlite')).toBe('logs/db/x.sqlite');
    expect(posix.join('a', './b', '', 'c')).toBe('a/b/c');
    expect(posix.join('a//b', 'c')).toBe('a/b/c');
  });

  it('先頭の / は絶対パスとして扱わない（resolve は扱う）', () => {
    expect(posix.join('/var', '/log')).toBe('/var/log');
    expect(posix.resolve('/a', 'b', '/c', 'd')).toBe('/c/d');
    expect(posix.resolve('/a/b/', '../c')).toBe('/a/c');
  });

  it('ルートより上には戻れず、相対パスでは .. が残る', () => {
    expect(posix.join('/a', '..', '..', 'b')).toBe('/b');
    expect(posix.join('..', 'a')).toBe('../a');
    expect(posix.join('a', '..', '..')).toBe('..');
  });

  it('引数なしや空になる結果は "." で、末尾の区切りは残る', () => {
    expect(join()).toBe('.');
    expect(join('a', '..')).toBe('.');
    expect(posix.join('a', 'b/')).toBe('a/b/');
    expect(posix.join('a/', '/b/')).toBe('a/b/');
  });

  it('resolve は現在の作業ディレクトリを基準に絶対パスにする', () => {
    const abs = resolve('logs', 'x.log');
    expect(abs).toBe(join(process.cwd(), 'logs', 'x.log'));
    expect(abs.startsWith(sep) || /^[A-Za-z]:/.test(abs)).toBe(true);
  });

  it('文字列以外は TypeError', () => {
    // @ts-expect-error 型エラーになる引数を実行時にも検証する
    expect(() => join('a', 1)).toThrowError(TypeError);
    // @ts-expect-error 型エラーになる引数を実行時にも検証する
    expect(() => join('a', undefined)).toThrowError(TypeError);
  });

  it('posix / win32 は OS によらず固定の区切りを使う', () => {
    expect(posix.join('a', 'b')).toBe('a/b');
    expect(win32.join('a', 'b')).toBe('a\\b');
    expect(win32.join('C:\\a', '..\\b')).toBe('C:\\b');
    expect(posix.join('C:\\a', 'b')).toBe('C:\\a/b'); // posix では \ は区切りではない
  });

  it('URL を join するとスキームの // が潰れる', () => {
    expect(posix.join('https://x.com', 'a')).toBe('https:/x.com/a');
  });
});
