// カード async-limit-concurrency の Contract を検証するテスト
import { Semaphore } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

/** マイクロタスクを消化して待機中の Promise を進める */
const flush = () => new Promise<void>((resolve) => queueMicrotask(resolve));

describe('async-limit-concurrency: Semaphore', () => {
  it('空きがあれば即 resolve し、available が減る', async () => {
    const sem = new Semaphore(2);
    expect(sem.capacity).toBe(2);
    expect(sem.available).toBe(2);
    await sem.acquire();
    expect(sem.available).toBe(1);
  });

  it('空きが無ければ release されるまで待つ', async () => {
    const sem = new Semaphore(1);
    await sem.acquire();
    let acquired = false;
    const waiting = sem.acquire().then(() => {
      acquired = true;
    });
    await flush();
    expect(acquired).toBe(false);
    sem.release();
    await waiting;
    expect(acquired).toBe(true);
    expect(sem.available).toBe(0); // permit は待機者へ直接渡り、available は変わらない
  });

  it('待機は呼び出し順（FIFO）に解放される', async () => {
    const sem = new Semaphore(1);
    await sem.acquire();
    const order: string[] = [];
    const a = sem.acquire().then(() => order.push('a'));
    const b = sem.acquire().then(() => order.push('b'));
    sem.release();
    await a;
    expect(order).toEqual(['a']);
    sem.release();
    await b;
    expect(order).toEqual(['a', 'b']);
  });

  it('release は待機者がいなければ available を増やし、capacity を超えない', async () => {
    const sem = new Semaphore(2);
    await sem.acquire();
    sem.release();
    expect(sem.available).toBe(2);
    sem.release(); // 余分な release は無視される
    expect(sem.available).toBe(2);
  });

  it('同時実行数が capacity を超えない', async () => {
    const sem = new Semaphore(2);
    let running = 0;
    let peak = 0;
    const task = async () => {
      await sem.acquire();
      try {
        running++;
        peak = Math.max(peak, running);
        await flush();
        running--;
      } finally {
        sem.release();
      }
    };
    await Promise.all([task(), task(), task(), task(), task()]);
    expect(peak).toBe(2);
    expect(sem.available).toBe(2);
  });

  it('release し忘れると以後の acquire は resolve しない', async () => {
    const sem = new Semaphore(1);
    await sem.acquire();
    let acquired = false;
    void sem.acquire().then(() => {
      acquired = true;
    });
    await flush();
    await flush();
    expect(acquired).toBe(false);
  });
});
