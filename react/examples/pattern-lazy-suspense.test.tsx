// カード pattern-lazy-suspense の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import { Component, lazy, Suspense, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

/** 手動で解決できる遅延ローダー。実際は lazy(() => import('./Heavy')) と書く */
function createDeferredLoader<P>(component: React.ComponentType<P>) {
  let resolve!: () => void;
  let reject!: (e: Error) => void;
  const promise = new Promise<{ default: React.ComponentType<P> }>((res, rej) => {
    resolve = () => res({ default: component });
    reject = rej;
  });
  const loader = vi.fn(() => promise);
  return { loader, resolve, reject };
}

function Heavy({ label }: { label: string }) {
  return <p>heavy: {label}</p>;
}

class Boundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    return this.state.error ? <p>error: {this.state.error.message}</p> : this.props.children;
  }
}

describe('pattern-lazy-suspense', () => {
  afterEach(cleanup);

  it('読み込みが終わるまで fallback を表示し、終わったら props 付きでコンポーネントを描画する', async () => {
    const { loader, resolve } = createDeferredLoader(Heavy);
    const LazyHeavy = lazy(loader);
    render(
      <Suspense fallback={<p>loading</p>}>
        <LazyHeavy label="a" />
      </Suspense>,
    );
    expect(screen.getByText('loading')).toBeInTheDocument();
    expect(screen.queryByText('heavy: a')).not.toBeInTheDocument();
    resolve();
    expect(await screen.findByText('heavy: a')).toBeInTheDocument();
    expect(screen.queryByText('loading')).not.toBeInTheDocument();
  });

  it('同じ Suspense の中にある準備済みの兄弟も、読み込み中は表示されない', async () => {
    const { loader, resolve } = createDeferredLoader(Heavy);
    const LazyHeavy = lazy(loader);
    render(
      <>
        <p>outside</p>
        <Suspense fallback={<p>loading</p>}>
          <p>inside</p>
          <LazyHeavy label="a" />
        </Suspense>
      </>,
    );
    expect(screen.getByText('outside')).toBeInTheDocument(); // 境界の外は影響を受けない
    expect(screen.queryByText('inside')).not.toBeInTheDocument();
    resolve();
    await screen.findByText('heavy: a');
    expect(screen.getByText('inside')).toBeInTheDocument();
  });

  it('ローダーは 1 回しか呼ばれず、再レンダーや再マウントでは読み込み直さない', async () => {
    const { loader, resolve } = createDeferredLoader(Heavy);
    const LazyHeavy = lazy(loader);
    const ui = (label: string) => (
      <Suspense fallback={<p>loading</p>}>
        <LazyHeavy label={label} />
      </Suspense>
    );
    const { rerender, unmount } = render(ui('a'));
    resolve();
    await screen.findByText('heavy: a');
    rerender(ui('b'));
    expect(screen.getByText('heavy: b')).toBeInTheDocument(); // fallback に戻らない
    unmount();
    render(ui('c'));
    expect(screen.getByText('heavy: c')).toBeInTheDocument(); // 2 回目のマウントは同期的に描画される
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it('読み込みに失敗すると例外として投げられ、Error Boundary で捕まえられる', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { loader, reject } = createDeferredLoader(Heavy);
    const LazyHeavy = lazy(loader);
    render(
      <Boundary>
        <Suspense fallback={<p>loading</p>}>
          <LazyHeavy label="a" />
        </Suspense>
      </Boundary>,
    );
    reject(new Error('chunk load failed'));
    expect(await screen.findByText('error: chunk load failed')).toBeInTheDocument();
    errorSpy.mockRestore();
  });
});
