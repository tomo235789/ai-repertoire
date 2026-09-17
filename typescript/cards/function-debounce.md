---
id: function-debounce
lang: typescript
title: 連続する呼び出しを最後の 1 回にまとめる
tags: [デバウンス, 間引き, 入力待ち, 連続呼び出し, debounce, coalesce, delay-call]
lib: es-toolkit
fn: debounce
since: "1.20.0"
verified: 2026-09-17
status: public
---

呼び出しが止まってから `debounceMs` 経つまで実行を遅らせ、連続する呼び出しを 1 回にまとめる。検索ボックスの入力やリサイズイベントの処理に使う。

## Signature

```ts
function debounce<F extends (...args: any[]) => void>(func: F, debounceMs: number, { signal, edges }?: DebounceOptions): DebouncedFunction<F>
```

## Usage

```ts
import { debounce } from 'es-toolkit';

const save = debounce((text: string) => console.log('save', text), 300);
save('a');
save('ab');
save('abc');
// => 最後の呼び出しから 300ms 後に 'save abc' が 1 回だけ出る
save.cancel(); // 保留中の実行を破棄
```

## Contract

- 既定（`edges` 省略 = `['trailing']`）では、最後の呼び出しから `debounceMs` 後に **最後の引数** で 1 回だけ実行する。途中の呼び出しはタイマーを張り直すだけで実行されない
- `edges: ['leading']` は最初の呼び出しを即時実行し、その後 `debounceMs` 以内の呼び出しは捨てる。`['leading', 'trailing']` は最初を即時実行し、待機中に 2 回目以降の呼び出しがあったときだけ末尾でもう 1 回実行する（1 回しか呼ばれなければ末尾は実行されない）
- `cancel()` はタイマーと保留中の引数を破棄する。`flush()` は保留中の呼び出しがあればその場で実行し、無ければ何もしない。`schedule()` はタイマーだけを張り直す
- `signal` が abort されると `cancel()` と同じ処理が走り、以後の呼び出しはすべて無視される
- 呼び出し時の `this` を保持して `func` に渡す。戻り値は常に `undefined`（`func` の戻り値は捨てられる）
- 状態（タイマー・保留引数）は返された関数ごとに持つ。`func` 自体は変更しない

## Alternatives

- 一定間隔で必ず実行したい（スクロール位置の追従など）なら `throttle`（カード function-throttle）
- 依存を増やせない場合は `setTimeout` / `clearTimeout` で自前実装できるが、`this`・`edges`・`AbortSignal` の扱いを揃えるのは手間なので推奨しない
- lodash からの移行は `es-toolkit/compat` の `debounce`（`leading` / `trailing` / `maxWait` オプションと戻り値の返却に対応）

## Pitfalls

- lodash の `{ leading: true, trailing: false }` は es-toolkit では `{ edges: ['leading'] }` と書く。真偽値オプションは無い
- lodash と違い戻り値を返さない。結果が要るなら `func` 側で状態に書き込む
- `maxWait` は無い。呼び出しが続く限り実行が先送りされるので、上限が要るなら `throttle` を使う
- React などで再レンダーごとに `debounce(...)` を作り直すと状態が毎回リセットされ、まとめられない。`useMemo` / モジュールスコープで 1 回だけ作る

## Test

`examples/function-debounce.test.ts`
