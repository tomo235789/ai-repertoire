// カード error-cause-chain の Contract を検証するテスト
import { inspect } from 'node:util';
import { describe, expect, it } from 'vitest';

/** cause を辿って根本原因を返す（深さの上限つき） */
const rootCause = (err: unknown, maxDepth = 10): unknown => {
  let current = err;
  for (let i = 0; i < maxDepth && current instanceof Error && current.cause !== undefined; i++) current = current.cause;
  return current;
};

describe('error-cause-chain: Error.cause', () => {
  it('cause には任意の値を渡せる', () => {
    const inner = new SyntaxError('bad json');
    expect(new Error('outer', { cause: inner }).cause).toBe(inner);
    expect(new Error('outer', { cause: 'plain' }).cause).toBe('plain');
    expect(new TypeError('t', { cause: 1 }).cause).toBe(1);
  });

  it('options.cause を渡したときだけ cause プロパティが作られる', () => {
    expect('cause' in new Error('x')).toBe(false);
    expect('cause' in new Error('x', {})).toBe(false);
    const withUndefined = new Error('x', { cause: undefined });
    expect('cause' in withUndefined).toBe(true);
    expect(withUndefined.cause).toBeUndefined();
  });

  it('cause は列挙されず、JSON.stringify では message ごと消える', () => {
    const err = new Error('outer', { cause: new Error('inner') });
    expect(Object.keys(err)).toEqual([]);
    expect(JSON.stringify(err)).toBe('{}');
    expect(JSON.stringify({ err })).toBe('{"err":{}}');
    expect({ ...err }).toEqual({});
  });

  it('cause を辿って根本原因に届く。Error 以外の値でも止まる', () => {
    const chain = new Error('top', { cause: new Error('mid', { cause: new RangeError('bottom') }) });
    expect((rootCause(chain) as Error).message).toBe('bottom');
    const stringBottom = new Error('top', { cause: new Error('mid', { cause: 'disk full' }) });
    expect(rootCause(stringBottom)).toBe('disk full');
    expect(rootCause('not an error')).toBe('not an error');
  });

  it('cause が自分自身でも深さの上限で止まる', () => {
    const loop = new Error('loop');
    loop.cause = loop;
    expect(rootCause(loop, 5)).toBe(loop);
  });

  it('util.inspect は [cause] を入れ子で表示する', () => {
    const err = new Error('top', { cause: new Error('mid', { cause: 'bottom' }) });
    const lines = inspect(err).split('\n');
    expect(lines[0]).toBe('Error: top');
    const mid = lines.find((l) => l.includes('[cause]: Error: mid'))!;
    const bottom = lines.find((l) => l.includes("[cause]: 'bottom'"))!;
    expect(mid).toMatch(/^ {2}\[cause\]/);
    expect(bottom).toMatch(/^ {4}\[cause\]/); // 1 段深くインデントされる
  });

  it('包み直しても元の stack と型は cause に残る', () => {
    const wrap = () => {
      try {
        JSON.parse('{oops');
      } catch (cause) {
        throw new Error('設定ファイルを読めなかった', { cause });
      }
    };
    const err = (() => {
      try {
        wrap();
      } catch (e) {
        return e as Error;
      }
    })();
    expect(err!.message).toBe('設定ファイルを読めなかった');
    expect(err!.cause).toBeInstanceOf(SyntaxError);
    expect((err!.cause as Error).stack).toMatch(/^SyntaxError: /);
  });
});
