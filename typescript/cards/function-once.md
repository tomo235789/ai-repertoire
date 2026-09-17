---
id: function-once
lang: typescript
title: 関数を 1 回だけ実行する
tags: [一度だけ, 初回のみ, 初期化, 遅延初期化, once, single-call, lazy-init]
lib: es-toolkit
fn: once
since: "1.30.0"
verified: 2026-09-17
status: public
---

最初の呼び出しだけ関数を実行し、以後は最初の戻り値を返し続ける。初期化処理やイベントリスナーの登録を 1 回に限定するのに使う。

## Signature

```ts
function once<F extends (...args: any[]) => any>(func: F): F
```

## Usage

```ts
import { once } from 'es-toolkit';

const init = once((name: string) => { console.log('init', name); return { name }; });
const a = init('first');  // 'init first' が出る
const b = init('second'); // 何も出ない。a と同じオブジェクトが返る
a === b; // => true
```

## Contract

- 1 回目の呼び出しで `func` を実行し、戻り値を保存する。2 回目以降は `func` を呼ばず **1 回目の戻り値（同じ参照）** を返す
- 2 回目以降の引数は無視される
- 1 回目に `func` が例外を投げても「実行済み」と記録され、2 回目以降は `func` を呼ばず `undefined` を返す
- `this` は `func` に渡されない（`func` は通常の関数として呼ばれる）
- 状態は返された関数ごとに持つ。`func` 自体は変更しない

## Alternatives

- 引数ごとに結果を使い回したいなら `memoize`（カード function-memoize）
- 非同期の初期化を 1 回にしたいなら、`Promise` を返す関数を `once` で包む（1 回目の `Promise` がそのまま共有される）
- lodash からの移行は `es-toolkit/compat` の `once`（挙動は同じ）

## Pitfalls

- 例外を投げた初期化は再試行されない。失敗時にやり直したいなら、`once` ではなく成功時にだけキャッシュする自前の関数を書く
- クラスのメソッドを `once(this.method)` のように包むと `this` が失われる。アロー関数で包むか `bind` してから渡す
- 呼び出し回数を数えたいだけなら `before` / `after`（es-toolkit）を検討する

## Test

`examples/function-once.test.ts`
