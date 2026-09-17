// カード pattern-error-boundary の実装。レンダー中の例外を捕まえて fallback を出すクラスコンポーネント
import { Component, type ErrorInfo, type ReactNode } from 'react';

export type ErrorBoundaryProps = {
  /** 例外発生時に表示する内容。reset を呼ぶと children を再描画する */
  fallback: (error: Error, reset: () => void) => ReactNode;
  /** この配列の要素が変わると自動でリセットする（ルート変更など） */
  resetKeys?: readonly unknown[];
  /** ログ送信など。componentDidCatch から呼ばれる */
  onError?: (error: Error, info: ErrorInfo) => void;
  children: ReactNode;
};

type State = { error: Error | null };

const sameKeys = (a: readonly unknown[] = [], b: readonly unknown[] = []) =>
  a.length === b.length && a.every((v, i) => Object.is(v, b[i]));

export class ErrorBoundary extends Component<ErrorBoundaryProps, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.onError?.(error, info);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (this.state.error !== null && !sameKeys(prevProps.resetKeys, this.props.resetKeys)) {
      this.reset();
    }
  }

  reset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    return error === null ? this.props.children : this.props.fallback(error, this.reset);
  }
}
