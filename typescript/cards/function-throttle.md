---
id: function-throttle
lang: typescript
title: 呼び出しを一定間隔に間引く
tags: [スロットル, 間引き, 一定間隔, 頻度制限, throttle, rate-limit, interval]
lib: es-toolkit
fn: throttle
since: "1.43.0"
verified: 2026-09-17
status: public
---

呼び出しが連続しても `throttleMs` に 1 回だけ実行する。スクロールやマウス移動のように止まらないイベントの処理に使う。

## Signature

```ts
function throttle<F extends (...args: any[]) => void>(func: F, throttleMs: number, { signal, edges }?: ThrottleOptions): ThrottledFunction<F>
```

## Usage

```ts
import { throttle } from 'es-toolkit';

const report = throttle((y: number) => console.log('scrollY', y), 200);
report(10); // 即時に 'scrollY 10'
report(20); // 200ms 以内なので間引かれる
report(30); // 最後の呼び出しから 200ms 後に 'scrollY 30'
report.cancel(); // 保留中の末尾実行を破棄
```

## Contract

- 既定（`edges` 省略 = `['leading', 'trailing']`）では最初の呼び出しを即時実行し、その後は前回の実行から `throttleMs` 以上経った呼び出しを即時実行する
- 間引かれた呼び出しがあれば、最後の呼び出しから `throttleMs` 後に **最後の引数** で末尾（trailing）実行する。末尾の実行時刻は「最後の呼び出し」を基準に測る
- `edges: ['leading']` は末尾実行をしない。`edges: ['trailing']` は最初の呼び出しも即時実行せず、末尾実行にまとめる
- `cancel()` は保留中の末尾実行を破棄する。`flush()` は保留中の末尾実行があればその場で実行する
- `signal` が abort されると保留中の末尾実行を破棄し、以後は間引き対象（前回の実行から `throttleMs` 未満）の呼び出しが無視される。`throttleMs` 以上経った呼び出しは abort 後も即時実行される
- 呼び出し時の `this` を保持して `func` に渡す。戻り値は常に `undefined`

## Alternatives

- 「止まってから 1 回だけ」実行したいなら `debounce`（カード function-debounce）。`throttle` は呼び続ける限り定期的に実行する点が違う
- 描画に同期させたいなら `requestAnimationFrame` でフレームごとに 1 回にまとめる
- lodash からの移行は `es-toolkit/compat` の `throttle`（`leading` / `trailing` オプション）

## Pitfalls

- lodash の `{ leading: false }` は es-toolkit では `{ edges: ['trailing'] }` と書く
- 末尾実行は「最後の呼び出しから `throttleMs` 後」に走る。lodash のように「区間の終わり」に固定されないので、間引かれる呼び出しが断続的に続くと末尾実行がその分遅れる
- 経過時間の判定に `Date.now()` を使う。テストで fake timers を使うときは `Date` も偽装されている必要がある（vitest の `vi.useFakeTimers()` は既定で偽装する）
- `signal` の abort は `throttle` を完全には止めない（末尾実行の破棄と間引き分の無視だけ）。呼び出し自体を止めたいなら呼び出し側で `signal.aborted` を確認する
- 戻り値を返さないので、結果が要るなら `func` 側で状態に書き込む

## Test

`examples/function-throttle.test.ts`
