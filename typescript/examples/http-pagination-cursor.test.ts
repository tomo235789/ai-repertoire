// カード http-pagination-cursor の Contract を検証するテスト
import { describe, expect, it, vi } from 'vitest';

type Page<T> = { items: T[]; nextCursor?: string };

async function* paginate<T>(fetchPage: (cursor?: string) => Promise<Page<T>>): AsyncGenerator<T> {
  let cursor: string | undefined;
  do {
    const page = await fetchPage(cursor);
    yield* page.items;
    cursor = page.nextCursor;
  } while (cursor !== undefined);
}

/** cursor → ページ の対応表から fetchPage を作る */
const pagesOf = <T>(table: Record<string, Page<T>>) =>
  vi.fn(async (cursor?: string): Promise<Page<T>> => table[cursor ?? 'first']!);

const threePages = () =>
  pagesOf<number>({
    first: { items: [1, 2], nextCursor: 'c1' },
    c1: { items: [3], nextCursor: 'c2' },
    c2: { items: [4, 5] },
  });

describe('http-pagination-cursor: async generator', () => {
  it('1 ページ目は cursor なしで取り、nextCursor が無くなるまで要素を順に yield する', async () => {
    const fetchPage = threePages();
    const seen: number[] = [];
    for await (const item of paginate(fetchPage)) seen.push(item);
    expect(seen).toEqual([1, 2, 3, 4, 5]);
    expect(fetchPage.mock.calls).toEqual([[undefined], ['c1'], ['c2']]);
  });

  it('遅延評価で、最初の next() まで fetchPage を呼ばず、次のページはページを消費し切ってから取る', async () => {
    const fetchPage = threePages();
    const gen = paginate(fetchPage);
    expect(fetchPage).not.toHaveBeenCalled();
    expect(await gen.next()).toEqual({ value: 1, done: false });
    expect(fetchPage).toHaveBeenCalledTimes(1);
    await gen.next(); // 2
    expect(fetchPage).toHaveBeenCalledTimes(1);
    await gen.next(); // 3（2 ページ目）
    expect(fetchPage).toHaveBeenCalledTimes(2);
  });

  it('break で抜けると return() が呼ばれ、以降のページは取らず finally も実行される', async () => {
    const fetchPage = threePages();
    let finallyRan = false;
    async function* wrapped() {
      try {
        yield* paginate(fetchPage);
      } finally {
        finallyRan = true;
      }
    }
    const seen: number[] = [];
    for await (const item of wrapped()) {
      seen.push(item);
      if (item === 3) break;
    }
    expect(seen).toEqual([1, 2, 3]);
    expect(fetchPage).toHaveBeenCalledTimes(2);
    expect(finallyRan).toBe(true);
  });

  it('fetchPage が reject するとそのエラーが for await の位置で throw される', async () => {
    const boom = new Error('network');
    const run = async () => {
      for await (const _ of paginate(async () => Promise.reject(boom))) {
        // 到達しない
      }
    };
    await expect(run()).rejects.toBe(boom);
  });

  it('items が空で nextCursor があるページは何も yield せず次へ進む', async () => {
    const fetchPage = pagesOf<string>({ first: { items: [], nextCursor: 'c1' }, c1: { items: ['a'] } });
    expect(await Array.fromAsync(paginate(fetchPage))).toEqual(['a']);
    expect(fetchPage).toHaveBeenCalledTimes(2);
  });

  it('nextCursor が null の API は undefined と比較すると無限ループするので正規化する', async () => {
    const nullApi = vi.fn(async (_cursor?: string): Promise<{ items: number[]; nextCursor: string | null }> => ({ items: [1], nextCursor: null }));
    const seen: number[] = [];
    for await (const item of paginate(nullApi as unknown as (c?: string) => Promise<Page<number>>)) {
      seen.push(item);
      if (seen.length === 3) break; // 止めなければ続く
    }
    expect(nullApi).toHaveBeenCalledTimes(3);
    const normalized = async (c?: string) => {
      const page = await nullApi(c);
      return { items: page.items, nextCursor: page.nextCursor ?? undefined };
    };
    expect(await Array.fromAsync(paginate(normalized))).toEqual([1]);
  });

  it('使い切った generator は再利用できない', async () => {
    const gen = paginate(threePages());
    await Array.fromAsync(gen);
    expect(await gen.next()).toEqual({ value: undefined, done: true });
  });
});
