// カード pattern-fetch-with-abort の実装。effect でデータ取得し、依存変更・アンマウント時に abort する
import { useEffect, useState } from 'react';

export type FetchState<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

/** url の JSON を取得する。url が変わると前回のリクエストを abort し、古いレスポンスで state を上書きしない */
export function useFetch<T>(url: string, fetchFn: typeof fetch = fetch): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({ status: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: 'loading' });
    fetchFn(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<T>;
      })
      .then((data) => {
        if (!controller.signal.aborted) setState({ status: 'success', data });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return; // abort 済み（古いリクエスト）は無視
        setState({ status: 'error', error: error instanceof Error ? error : new Error(String(error)) });
      });
    return () => controller.abort();
  }, [url, fetchFn]);

  return state;
}
