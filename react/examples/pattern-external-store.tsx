// カード pattern-external-store の実装。React 外のストアを useSyncExternalStore で購読する
import { useMemo, useSyncExternalStore } from 'react';

export type Store<T> = {
  getSnapshot: () => T;
  setState: (updater: T | ((prev: T) => T)) => void;
  subscribe: (listener: () => void) => () => void;
};

/** 最小のストア。snapshot は不変オブジェクトとして扱い、setState のたびに新しい参照になる */
export function createStore<T>(initial: T): Store<T> {
  let state = initial;
  const listeners = new Set<() => void>();
  return {
    getSnapshot: () => state,
    setState: (updater) => {
      const next = typeof updater === 'function' ? (updater as (prev: T) => T)(state) : updater;
      if (Object.is(next, state)) return;
      state = next;
      listeners.forEach((l) => l());
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

const identity = <T,>(x: T): T => x;

/**
 * selector が返す値が Object.is で変わったときだけ再レンダーする。サーバーでは getServerSnapshot を使う。
 * ストアのスナップショットが同じ間は selector の結果をキャッシュして同じ参照を返すので、
 * `(s) => ({ theme: s.theme })` のようにオブジェクトを作る selector でも getSnapshot の結果が安定する
 */
export function useStore<T, S = T>(store: Store<T>, selector: (state: T) => S = identity as (state: T) => S, getServerSnapshot?: () => T): S {
  const select = useMemo(() => cachedSelector(selector), [selector]);
  return useSyncExternalStore(
    store.subscribe,
    () => select(store.getSnapshot()),
    getServerSnapshot ? () => select(getServerSnapshot()) : undefined,
  );
}

/** 直前の入力と Object.is で同じなら前回の結果を返す selector に包む（純粋関数。キャッシュは返す関数のクロージャに閉じる） */
export function cachedSelector<T, S>(selector: (state: T) => S): (state: T) => S {
  let cache: { source: T; selected: S } | null = null;
  return (source) => {
    if (cache !== null && Object.is(cache.source, source)) return cache.selected;
    const selected = selector(source);
    cache = { source, selected };
    return selected;
  };
}
