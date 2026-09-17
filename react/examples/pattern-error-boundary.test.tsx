// カード pattern-error-boundary の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from 'vitest';
import { ErrorBoundary } from './pattern-error-boundary';

function Bomb({ explode }: { explode: boolean }) {
  if (explode) throw new Error('boom');
  return <p>safe</p>;
}

const fallback = (error: Error, reset: () => void) => (
  <div>
    <p>fallback: {error.message}</p>
    <button onClick={reset}>retry</button>
  </div>
);

describe('pattern-error-boundary', () => {
  let errorSpy: MockInstance;
  beforeEach(() => {
    // React が捕捉した例外を console.error に出すので抑止する
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    cleanup();
    errorSpy.mockRestore();
  });

  it('子のレンダー中の例外を捕まえ、children の代わりに fallback を表示する。onError に error と componentStack が渡る', () => {
    const onError = vi.fn();
    render(
      <ErrorBoundary fallback={fallback} onError={onError}>
        <p>sibling</p>
        <Bomb explode />
      </ErrorBoundary>,
    );
    expect(screen.getByText('fallback: boom')).toBeInTheDocument();
    expect(screen.queryByText('sibling')).not.toBeInTheDocument(); // 境界の中は丸ごと置き換わる
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error);
    expect(onError.mock.calls[0][1].componentStack).toContain('Bomb');
  });

  it('例外が無ければ children をそのまま表示する', () => {
    render(
      <ErrorBoundary fallback={fallback}>
        <Bomb explode={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('fallback から reset を呼ぶと children を再描画する。まだ例外が出るなら再び fallback になる', async () => {
    const user = userEvent.setup();
    function Page() {
      const [explode, setExplode] = useState(true);
      return (
        <>
          <button onClick={() => setExplode(false)}>fix</button>
          <ErrorBoundary fallback={fallback}>
            <Bomb explode={explode} />
          </ErrorBoundary>
        </>
      );
    }
    render(<Page />);
    expect(screen.getByText('fallback: boom')).toBeInTheDocument();
    await user.click(screen.getByText('retry'));
    expect(screen.getByText('fallback: boom')).toBeInTheDocument(); // 原因が残っていれば再度捕まえる
    await user.click(screen.getByText('fix'));
    await user.click(screen.getByText('retry'));
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('resetKeys の要素が変わると自動でリセットする', () => {
    const { rerender } = render(
      <ErrorBoundary fallback={fallback} resetKeys={['/a']}>
        <Bomb explode />
      </ErrorBoundary>,
    );
    expect(screen.getByText('fallback: boom')).toBeInTheDocument();
    rerender(
      <ErrorBoundary fallback={fallback} resetKeys={['/a']}>
        <Bomb explode={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText('fallback: boom')).toBeInTheDocument(); // 同じ keys ではリセットしない
    rerender(
      <ErrorBoundary fallback={fallback} resetKeys={['/b']}>
        <Bomb explode={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('イベントハンドラ内の例外は捕まえない（window の error イベントに届く）', async () => {
    const user = userEvent.setup();
    const onWindowError = vi.fn((e: ErrorEvent) => e.preventDefault());
    window.addEventListener('error', onWindowError);
    const onError = vi.fn();
    render(
      <ErrorBoundary fallback={fallback} onError={onError}>
        <button
          onClick={() => {
            throw new Error('handler');
          }}
        >
          click
        </button>
      </ErrorBoundary>,
    );
    await user.click(screen.getByText('click'));
    expect(screen.getByText('click')).toBeInTheDocument(); // fallback にならない
    expect(onError).not.toHaveBeenCalled();
    expect(onWindowError).toHaveBeenCalledTimes(1);
    expect(onWindowError.mock.calls[0][0].error.message).toBe('handler');
    window.removeEventListener('error', onWindowError);
  });
});
