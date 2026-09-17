// カード pattern-fetch-with-abort の Contract を検証するテスト
import { act, cleanup, render, screen } from '@testing-library/react';
import { StrictMode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useFetch } from './pattern-fetch-with-abort';

type User = { name: string };

/** レスポンスを手動で解決できる fetch モック。abort されると AbortError で reject する（実 fetch と同じ） */
function createFetchMock(options: { honorAbort: boolean } = { honorAbort: true }) {
  type Pending = {
    resolve: (body: unknown, status?: number) => void;
    reject: (error: unknown) => void;
    signal: AbortSignal;
    json: ReturnType<typeof vi.fn>;
  };
  const pending = new Map<string, Pending>();
  const fetchFn = vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    const signal = init!.signal!;
    return new Promise<Response>((resolve, reject) => {
      const json = vi.fn();
      pending.set(url, {
        signal,
        json,
        reject,
        resolve: (body, status = 200) => {
          json.mockImplementation(async () => body);
          resolve({ ok: status >= 200 && status < 300, status, json } as unknown as Response);
        },
      });
      if (options.honorAbort) {
        signal.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
      }
    });
  }) as unknown as typeof fetch;
  const resolve = async (url: string, body: unknown, status = 200) => {
    await act(async () => {
      pending.get(url)!.resolve(body, status);
    });
  };
  const reject = async (url: string, error: unknown) => {
    await act(async () => {
      pending.get(url)!.reject(error);
    });
  };
  return {
    fetchFn,
    resolve,
    reject,
    signalOf: (url: string) => pending.get(url)!.signal,
    jsonOf: (url: string) => pending.get(url)!.json,
    calls: () => (fetchFn as ReturnType<typeof vi.fn>).mock.calls,
  };
}

function UserName({ url, fetchFn }: { url: string; fetchFn: typeof fetch }) {
  const state = useFetch<User>(url, fetchFn);
  if (state.status === 'loading') return <p>loading</p>;
  if (state.status === 'error') return <p>error: {state.error.message}</p>;
  return <p>name: {state.data.name}</p>;
}

describe('pattern-fetch-with-abort', () => {
  afterEach(cleanup);

  it('マウント時に signal 付きで fetch し、解決後に success になる', async () => {
    const mock = createFetchMock();
    render(<UserName url="/users/1" fetchFn={mock.fetchFn} />);
    expect(screen.getByText('loading')).toBeInTheDocument();
    expect(mock.calls()[0][1].signal).toBeInstanceOf(AbortSignal);
    await mock.resolve('/users/1', { name: 'alice' });
    expect(screen.getByText('name: alice')).toBeInTheDocument();
  });

  it('url が変わると前のリクエストを abort し、loading に戻る', async () => {
    const mock = createFetchMock();
    const { rerender } = render(<UserName url="/users/1" fetchFn={mock.fetchFn} />);
    await mock.resolve('/users/1', { name: 'alice' });
    rerender(<UserName url="/users/2" fetchFn={mock.fetchFn} />);
    expect(mock.signalOf('/users/1').aborted).toBe(true);
    expect(screen.getByText('loading')).toBeInTheDocument();
    await mock.resolve('/users/2', { name: 'bob' });
    expect(screen.getByText('name: bob')).toBeInTheDocument();
  });

  it('古いレスポンスが後から届いても state を上書きしない（abort を無視する fetch でも同じ）', async () => {
    const mock = createFetchMock({ honorAbort: false });
    const { rerender } = render(<UserName url="/users/1" fetchFn={mock.fetchFn} />);
    rerender(<UserName url="/users/2" fetchFn={mock.fetchFn} />);
    await mock.resolve('/users/2', { name: 'bob' });
    await mock.resolve('/users/1', { name: 'alice' }); // 遅れて届いた古いレスポンス
    expect(screen.getByText('name: bob')).toBeInTheDocument();
  });

  it('アンマウント時に abort し、その後のレスポンス・AbortError で state を更新しない', async () => {
    const mock = createFetchMock();
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { unmount } = render(<UserName url="/users/1" fetchFn={mock.fetchFn} />);
    unmount();
    expect(mock.signalOf('/users/1').aborted).toBe(true);
    await act(async () => {}); // AbortError の reject が処理されるのを待つ
    expect(errorSpy).not.toHaveBeenCalled(); // unhandled rejection や unmounted 更新の警告が無い
    errorSpy.mockRestore();
  });

  it('非 2xx（res.ok が偽）は res.json() を読まずに HTTP エラーとして error になる', async () => {
    const mock = createFetchMock();
    render(<UserName url="/users/404" fetchFn={mock.fetchFn} />);
    await mock.resolve('/users/404', { message: 'not found' }, 404);
    expect(screen.getByText('error: HTTP 404')).toBeInTheDocument();
    expect(mock.jsonOf('/users/404')).not.toHaveBeenCalled();
  });

  it('fetch が reject（ネットワークエラーなど）すると error になる。Error 以外は Error に包む', async () => {
    const mock = createFetchMock();
    const { rerender } = render(<UserName url="/users/1" fetchFn={mock.fetchFn} />);
    await mock.reject('/users/1', new TypeError('Failed to fetch'));
    expect(screen.getByText('error: Failed to fetch')).toBeInTheDocument();
    rerender(<UserName url="/users/2" fetchFn={mock.fetchFn} />);
    await mock.reject('/users/2', 'plain string');
    expect(screen.getByText('error: plain string')).toBeInTheDocument();
  });

  it('StrictMode（開発時）では effect が 2 回走り fetch も 2 回呼ばれるが、1 回目は abort され 2 回目の結果だけが使われる', async () => {
    const mock = createFetchMock();
    render(
      <StrictMode>
        <UserName url="/users/1" fetchFn={mock.fetchFn} />
      </StrictMode>,
    );
    const calls = mock.calls();
    expect(calls).toHaveLength(2);
    expect(calls[0][1].signal.aborted).toBe(true);
    expect(calls[1][1].signal.aborted).toBe(false);
    await mock.resolve('/users/1', { name: 'alice' }); // 2 回目の pending が残っている
    expect(screen.getByText('name: alice')).toBeInTheDocument();
  });
});
