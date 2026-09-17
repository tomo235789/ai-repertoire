// カード pattern-effect-cleanup の Contract を検証するテスト
import { act, cleanup, render } from '@testing-library/react';
import { StrictMode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useInterval, useSubscription, type Subscribable } from './pattern-effect-cleanup';

function Ticker({ onTick, delayMs }: { onTick: () => void; delayMs: number | null }) {
  useInterval(onTick, delayMs);
  return null;
}

/** テスト用の購読元。現在のリスナー数を数えられる */
function createSource<T>(): Subscribable<T> & { emit: (v: T) => void; listenerCount: () => number } {
  const listeners = new Set<(v: T) => void>();
  return {
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    emit: (v) => listeners.forEach((l) => l(v)),
    listenerCount: () => listeners.size,
  };
}

function Subscriber({ source, onValue, log }: { source: Subscribable<string>; onValue: (v: string) => void; log: string[] }) {
  useSubscription(source, onValue, log);
  return null;
}

describe('pattern-effect-cleanup', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it('effect はマウント後に走り、タイマーは delayMs ごとに発火する', () => {
    const onTick = vi.fn();
    render(<Ticker onTick={onTick} delayMs={100} />);
    expect(onTick).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(250));
    expect(onTick).toHaveBeenCalledTimes(2);
  });

  it('アンマウント時に cleanup が走り、以後タイマーは発火しない', () => {
    const onTick = vi.fn();
    const { unmount } = render(<Ticker onTick={onTick} delayMs={100} />);
    act(() => vi.advanceTimersByTime(100));
    unmount();
    act(() => vi.advanceTimersByTime(1000));
    expect(onTick).toHaveBeenCalledTimes(1);
  });

  it('依存 (delayMs) が変わると cleanup → 再実行の順で走り、古いタイマーは残らない', () => {
    const onTick = vi.fn();
    const { rerender } = render(<Ticker onTick={onTick} delayMs={100} />);
    rerender(<Ticker onTick={onTick} delayMs={1000} />);
    act(() => vi.advanceTimersByTime(999));
    expect(onTick).not.toHaveBeenCalled(); // 100ms のタイマーは止まっている
    act(() => vi.advanceTimersByTime(1));
    expect(onTick).toHaveBeenCalledTimes(1);
  });

  it('delayMs が null ならタイマーを張らない', () => {
    const onTick = vi.fn();
    render(<Ticker onTick={onTick} delayMs={null} />);
    act(() => vi.advanceTimersByTime(10_000));
    expect(onTick).not.toHaveBeenCalled();
  });

  it('callback を差し替えてもタイマーは張り直されず、次の発火から新しい callback が使われる', () => {
    const first = vi.fn();
    const second = vi.fn();
    const { rerender } = render(<Ticker onTick={first} delayMs={100} />);
    act(() => vi.advanceTimersByTime(90));
    rerender(<Ticker onTick={second} delayMs={100} />);
    act(() => vi.advanceTimersByTime(10)); // 張り直されていれば発火しない
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });

  it('購読は effect で開始し cleanup で解除する。source が変わると cleanup → 再購読の順になる', () => {
    const a = createSource<string>();
    const b = createSource<string>();
    const onValue = vi.fn();
    const log: string[] = [];
    const { rerender, unmount } = render(<Subscriber source={a} onValue={onValue} log={log} />);
    expect(log).toEqual(['subscribe']);
    expect(a.listenerCount()).toBe(1);

    rerender(<Subscriber source={b} onValue={onValue} log={log} />);
    expect(log).toEqual(['subscribe', 'unsubscribe', 'subscribe']);
    expect(a.listenerCount()).toBe(0);
    expect(b.listenerCount()).toBe(1);

    act(() => a.emit('old'));
    act(() => b.emit('new'));
    expect(onValue.mock.calls).toEqual([['new']]);

    unmount();
    expect(b.listenerCount()).toBe(0);
  });

  it('StrictMode（開発時）ではマウント直後に effect → cleanup → effect と 1 回余分に走るが、購読数は 1 に収束する', () => {
    const source = createSource<string>();
    const log: string[] = [];
    const { unmount } = render(
      <StrictMode>
        <Subscriber source={source} onValue={() => {}} log={log} />
      </StrictMode>,
    );
    expect(log).toEqual(['subscribe', 'unsubscribe', 'subscribe']);
    expect(source.listenerCount()).toBe(1);
    unmount();
    expect(source.listenerCount()).toBe(0);
  });
});
