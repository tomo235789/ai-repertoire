// カード pattern-effect-cleanup の実装。effect で始めた購読・タイマーは cleanup で必ず止める
import { useEffect, useRef } from 'react';

/** delayMs ごとに callback を呼ぶ。null で停止。callback の変更ではタイマーを張り直さない */
export function useInterval(callback: () => void, delayMs: number | null): void {
  const savedCallback = useRef(callback);
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delayMs === null) return;
    const id = setInterval(() => savedCallback.current(), delayMs);
    return () => clearInterval(id);
  }, [delayMs]);
}

export type Subscribable<T> = {
  subscribe: (listener: (value: T) => void) => () => void;
};

/** source を購読し、値が来るたびに onValue を呼ぶ。source が変わると購読し直す */
export function useSubscription<T>(source: Subscribable<T>, onValue: (value: T) => void, log?: string[]): void {
  const savedOnValue = useRef(onValue);
  useEffect(() => {
    savedOnValue.current = onValue;
  }, [onValue]);

  useEffect(() => {
    log?.push('subscribe');
    const unsubscribe = source.subscribe((value) => savedOnValue.current(value));
    return () => {
      log?.push('unsubscribe');
      unsubscribe();
    };
  }, [source, log]);
}
