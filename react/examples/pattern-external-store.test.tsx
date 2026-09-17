// カード pattern-external-store の Contract を検証するテスト
import { act, cleanup, render, screen } from '@testing-library/react';
import { StrictMode, useSyncExternalStore } from 'react';
import { renderToString } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cachedSelector, createStore, useStore } from './pattern-external-store';

type Settings = { theme: 'light' | 'dark'; fontSize: number };
const initial: Settings = { theme: 'light', fontSize: 14 };

/** リスナー数を数えられるストア */
function createCountingStore<T>(init: T) {
  const store = createStore(init);
  let count = 0;
  const subscribe: typeof store.subscribe = (l) => {
    count++;
    const unsub = store.subscribe(l);
    return () => {
      count--;
      unsub();
    };
  };
  return { ...store, subscribe, listenerCount: () => count };
}

describe('pattern-external-store', () => {
  afterEach(cleanup);

  it('React 外で setState すると購読しているコンポーネントが再レンダーされる', () => {
    const store = createStore(initial);
    function Theme() {
      const theme = useStore(store, (s) => s.theme);
      return <p>theme: {theme}</p>;
    }
    render(<Theme />);
    expect(screen.getByText('theme: light')).toBeInTheDocument();
    act(() => store.setState((s) => ({ ...s, theme: 'dark' })));
    expect(screen.getByText('theme: dark')).toBeInTheDocument();
  });

  it('selector の結果が同じ間は再レンダーされない', () => {
    const store = createStore(initial);
    const renders: number[] = [];
    function Theme() {
      const theme = useStore(store, (s) => s.theme);
      renders.push(1);
      return <p>theme: {theme}</p>;
    }
    render(<Theme />);
    act(() => store.setState((s) => ({ ...s, fontSize: 16 }))); // 無関係なフィールドの更新
    expect(store.getSnapshot().fontSize).toBe(16);
    expect(renders).toHaveLength(1);
  });

  it('マウント時に購読し、アンマウント時に解除する。StrictMode でも購読数は 1 に収束する', () => {
    const store = createCountingStore(initial);
    function Theme() {
      return <p>{useStore(store, (s) => s.theme)}</p>;
    }
    const { unmount } = render(<Theme />);
    expect(store.listenerCount()).toBe(1);
    unmount();
    expect(store.listenerCount()).toBe(0);

    const strict = render(
      <StrictMode>
        <Theme />
      </StrictMode>,
    );
    expect(store.listenerCount()).toBe(1);
    strict.unmount();
    expect(store.listenerCount()).toBe(0);
  });

  it('サーバーレンダーでは getServerSnapshot の値が使われ、渡さないと例外になる', () => {
    const store = createStore(initial);
    function WithServer() {
      return <p>{useStore(store, (s) => s.theme, (): Settings => ({ ...initial, theme: 'dark' }))}</p>;
    }
    function WithoutServer() {
      return <p>{useStore(store, (s) => s.theme)}</p>;
    }
    expect(renderToString(<WithServer />)).toBe('<p>dark</p>');
    expect(() => renderToString(<WithoutServer />)).toThrow('Missing getServerSnapshot');
  });

  it('オブジェクトを作る selector でも、スナップショットが同じ間は Object.is で等しい参照を返す（無限ループにならない）', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const store = createStore(initial);
    const selectTheme = (s: Settings) => ({ theme: s.theme }); // 呼ぶたびに新しいオブジェクト
    const seen: { theme: string }[] = [];
    function Theme() {
      const selected = useStore(store, selectTheme);
      seen.push(selected);
      return <p>theme: {selected.theme}</p>;
    }
    const { rerender } = render(<Theme />);
    rerender(<Theme />); // 親の再レンダー。スナップショットは同じ
    expect(screen.getByText('theme: light')).toBeInTheDocument();
    expect(seen).toHaveLength(2);
    expect(Object.is(seen[0], seen[1])).toBe(true);
    expect(errorSpy).not.toHaveBeenCalled(); // getSnapshot should be cached の警告が出ない

    act(() => store.setState((s) => ({ ...s, theme: 'dark' }))); // スナップショットが変わると新しい結果
    expect(screen.getByText('theme: dark')).toBeInTheDocument();
    expect(Object.is(seen[0], seen[seen.length - 1])).toBe(false);
    errorSpy.mockRestore();
  });

  it('cachedSelector は入力が Object.is で同じ間は同じ結果を返し、入力が変わると再計算する', () => {
    const calls: Settings[] = [];
    const select = cachedSelector((s: Settings) => {
      calls.push(s);
      return { theme: s.theme };
    });
    const a = select(initial);
    expect(select(initial)).toBe(a);
    expect(calls).toHaveLength(1);
    const next: Settings = { ...initial, fontSize: 16 };
    const b = select(next);
    expect(b).not.toBe(a);
    expect(b).toEqual(a);
    expect(calls).toHaveLength(2);
  });

  it('getSnapshot が毎回新しいオブジェクトを返すと警告が出て無限ループになる', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const subscribe = () => () => {};
    function Broken() {
      const snapshot = useSyncExternalStore(subscribe, () => ({ theme: 'light' })); // 毎回別の参照
      return <p>{snapshot.theme}</p>;
    }
    expect(() => render(<Broken />)).toThrow('Maximum update depth exceeded');
    expect(errorSpy.mock.calls[0][0]).toContain('The result of getSnapshot should be cached');
    errorSpy.mockRestore();
  });
});
