---
id: pattern-error-boundary
lang: react
title: レンダー中の例外を Error Boundary で捕まえて代替表示する
tags: [例外処理, エラー境界, フォールバック, リセット, error-boundary, componentDidCatch, fallback, resetKeys]
lib: react
fn: componentDidCatch
since: "18.0"
verified: 2026-09-17
status: public
---

子コンポーネントのレンダー中に例外が出てもアプリ全体を白画面にしたくないとき。クラスコンポーネントで `getDerivedStateFromError` と `componentDidCatch` を実装し、fallback を表示してリセット手段を用意する。関数コンポーネントでは書けない。

## Signature

```tsx
class ErrorBoundary extends Component<{ fallback: (error: Error, reset: () => void) => ReactNode; resetKeys?: readonly unknown[]; onError?: (error: Error, info: ErrorInfo) => void; children: ReactNode }>
```

## Usage

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';
type Props = { fallback: (error: Error, reset: () => void) => ReactNode; resetKeys?: readonly unknown[]; onError?: (error: Error, info: ErrorInfo) => void; children: ReactNode };
class ErrorBoundary extends Component<Props, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }        // fallback に切り替える
  componentDidCatch(error: Error, info: ErrorInfo) { this.props.onError?.(error, info); } // ログ送信
  componentDidUpdate(prev: Props) { const a = prev.resetKeys ?? [], b = this.props.resetKeys ?? []; if (this.state.error && (a.length !== b.length || a.some((k, i) => !Object.is(k, b[i])))) this.reset(); } // keys が変われば自動リセット
  reset = () => this.setState({ error: null });
  render() { return this.state.error ? this.props.fallback(this.state.error, this.reset) : this.props.children; }
} // <ErrorBoundary fallback={(e, reset) => <button onClick={reset}>再試行: {e.message}</button>} resetKeys={[pathname]}>...</ErrorBoundary>
```

## Contract

- 子のレンダー中の例外を捕まえ、`children` の代わりに `fallback` を表示する。境界の中は兄弟も含めて丸ごと置き換わる
- `onError` には `Error` と `componentStack`（例外を投げたコンポーネント名を含む文字列）を持つ `ErrorInfo` が渡る
- 例外が無ければ `children` をそのまま表示する
- `fallback` から `reset` を呼ぶと `children` を再描画する。原因が残っていれば再び捕まえて `fallback` に戻る
- `resetKeys` の要素が変わる（`Object.is` 比較）と自動でリセットする。同じ値のままではリセットしない
- イベントハンドラ内の例外は捕まえない。`fallback` にならず `onError` も呼ばれず、`window` の `error` イベントに届く

## Alternatives

- `react-error-boundary` パッケージの `ErrorBoundary` / `useErrorBoundary` は同じ設計（`fallbackRender`、`resetKeys`、`onReset`）で、自前で書く必要が無ければそちらを使う
- イベントハンドラや非同期処理の例外は `try/catch` で state に入れ、レンダーで表示する。境界に渡したいなら `setState(() => { throw error })` でレンダー中に投げ直す
- ルート全体で捕捉するなら `createRoot(el, { onUncaughtError, onCaughtError })`（React 19）でログ送信を一元化できる

## Pitfalls

- 境界は「自分より下」の例外しか捕まえない。境界自身の `render` や `fallback` の中の例外は上の境界に伝わる
- 捕まえられないもの: イベントハンドラ、`setTimeout` などの非同期コールバック、SSR、境界自身の例外
- `reset` だけでは原因が直らない（同じ props で再描画されるだけ）。`resetKeys` にルートやクエリなど「変われば直る可能性がある値」を入れる
- React はテスト・開発環境で捕捉した例外も `console.error` に出す。テストでは `vi.spyOn(console, 'error')` で抑止する

## Test

`examples/pattern-error-boundary.test.tsx`
