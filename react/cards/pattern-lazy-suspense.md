---
id: pattern-lazy-suspense
lang: react
title: コンポーネントを遅延読み込みして読み込み中は fallback を出す
tags: [遅延読み込み, コード分割, サスペンス, 動的import, lazy, Suspense, code-splitting, fallback]
lib: react
fn: React.lazy
since: "18.0"
verified: 2026-09-17
status: public
---

初期表示に不要な重いコンポーネント（エディタ、チャート、モーダル）を別チャンクに分けて必要になってから読み込むとき。`lazy` で包み、`Suspense` の `fallback` で読み込み中の表示を決める。

## Signature

```tsx
function lazy<P>(load: () => Promise<{ default: ComponentType<P> }>): ComponentType<P>
function Suspense(props: { fallback?: ReactNode; children: ReactNode }): JSX.Element
```

## Usage

```tsx
import { lazy, Suspense } from 'react';
const HeavyChart = lazy(() => import('./HeavyChart')); // default export を持つモジュール

function Dashboard() {
  return (
    <Suspense fallback={<p>読み込み中…</p>}>
      <HeavyChart range="7d" />
    </Suspense>
  ); // => チャンクが届くまで fallback、届いたら HeavyChart が props 付きで描画される
}
```

## Contract

- 読み込みが終わるまで `fallback` を表示し、終わったら props 付きでコンポーネントを描画する。`fallback` は消える
- 同じ `Suspense` の中にある準備済みの兄弟も、読み込み中は表示されない（境界の中は丸ごと `fallback` になる）。境界の外は影響を受けない
- ローダーは 1 回しか呼ばれない。読み込み後の再レンダー（props 変更）で `fallback` に戻らず、アンマウント → 再マウントでも再読み込みせず同期的に描画される
- 読み込みに失敗（Promise の reject）すると例外として投げられ、上位の Error Boundary で捕まえられる

## Alternatives

- ルート単位の分割はルーターの機能（React Router の `lazy` ルート、Next.js の自動分割）を使う方が `Suspense` の配置を考えなくて済む
- 表示せずに事前読み込みだけしたいなら、hover 時などに `import('./HeavyChart')` を呼んでおく（モジュールキャッシュに載る）
- コンポーネントではなくデータの待機は `use(promise)` や TanStack Query の `useSuspenseQuery`。同じ `Suspense` 境界に統合できる

## Pitfalls

- `lazy(...)` はモジュールスコープ（コンポーネントの外）で 1 回だけ呼ぶ。レンダー中に呼ぶと毎回別のコンポーネントになり、再読み込みと再マウントを繰り返す
- named export は `lazy(() => import('./m').then((m) => ({ default: m.Chart })))` のように `default` に詰め替える
- `Suspense` の位置で「何がまとめて消えるか」が決まる。細かすぎると fallback が点滅し、大きすぎると準備済みの部分まで隠れる
- デプロイで古いチャンクが消えると読み込みが失敗する。Error Boundary で「再読み込み」導線を用意する（カード pattern-error-boundary）

## Test

`examples/pattern-lazy-suspense.test.tsx`
