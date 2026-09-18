// カード log-correlation-id の Contract を検証するテスト
import { AsyncLocalStorage } from 'node:async_hooks';
import { EventEmitter } from 'node:events';
import { describe, expect, it } from 'vitest';

const als = new AsyncLocalStorage<string>();
const tick = () => new Promise<void>((resolve) => setTimeout(resolve, 0));

describe('log-correlation-id: AsyncLocalStorage', () => {
  it('run の外では undefined、中と派生した非同期処理では同じ store を返す', async () => {
    expect(als.getStore()).toBeUndefined();
    const seen: (string | undefined)[] = [];
    await als.run('req-1', async () => {
      seen.push(als.getStore());
      await tick(); // setTimeout 越え
      seen.push(als.getStore());
      await Promise.resolve().then(() => seen.push(als.getStore()));
      seen.push(await new Promise<string | undefined>((resolve) => setImmediate(() => resolve(als.getStore()))));
    });
    expect(seen).toEqual(['req-1', 'req-1', 'req-1', 'req-1']);
    expect(als.getStore()).toBeUndefined();
  });

  it('run は callback を同期的に呼び、戻り値をそのまま返す', async () => {
    let calledSync = false;
    const result = als.run('sync', () => {
      calledSync = true;
      return 42;
    });
    expect(calledSync).toBe(true);
    expect(result).toBe(42);
    const p = als.run('async', async () => als.getStore());
    expect(p).toBeInstanceOf(Promise);
    expect(await p).toBe('async');
  });

  it('並行する run は独立していて混ざらない', async () => {
    const results = await Promise.all(
      ['a', 'b', 'c'].map((id, i) =>
        als.run(id, async () => {
          await new Promise((resolve) => setTimeout(resolve, (3 - i) * 2)); // 逆順に終わる
          return als.getStore();
        }),
      ),
    );
    expect(results).toEqual(['a', 'b', 'c']);
  });

  it('入れ子の run は内側で内側の store、抜けると外側に戻る', () => {
    als.run('outer', () => {
      als.run('inner', () => expect(als.getStore()).toBe('inner'));
      expect(als.getStore()).toBe('outer');
    });
  });

  it('callback が同期的に throw しても run が投げてコンテキストは戻る', () => {
    expect(() =>
      als.run('boom', () => {
        throw new Error('boom');
      }),
    ).toThrow('boom');
    expect(als.getStore()).toBeUndefined();
  });

  it('exit の中だけ undefined になり、外で登録したリスナーも emit した run の store を見る', () => {
    const emitter = new EventEmitter();
    let inListener: string | undefined = 'unset';
    emitter.on('ev', () => {
      inListener = als.getStore();
    });
    als.run('emit', () => {
      als.exit(() => expect(als.getStore()).toBeUndefined());
      expect(als.getStore()).toBe('emit');
      emitter.emit('ev');
    });
    expect(inListener).toBe('emit');
  });

  it('外で作った Promise を中で await しても store は見えるが、中で作ったコールバックを外で呼ぶと伝搬しない', async () => {
    const outside = tick();
    const inside = await als.run('req-2', async () => {
      await outside;
      return als.getStore();
    });
    expect(inside).toBe('req-2');
    let deferred: (() => string | undefined) | undefined;
    als.run('req-3', () => {
      deferred = () => als.getStore();
    });
    expect(deferred!()).toBeUndefined(); // 同期的に外から呼ぶと run の外
  });
});
