---
id: error-cause-chain
lang: typescript
title: エラーに原因を付けて包み直す
tags: [原因の連鎖, エラーのラップ, 文脈の追加, 根本原因, cause, error-wrapping, error-chain, root-cause]
lib: stdlib
fn: Error.cause
since: "ES2022"
verified: 2026-09-17
status: public
---

下位のエラーを `cause` に載せて上位の文脈を持つエラーを投げ直す。「何をしていて失敗したか」と「なぜ失敗したか」を両方残すために使う。

## Signature

```ts
new Error(message?: string, options?: { cause?: unknown }): Error  // err.cause: unknown
```

## Usage

```ts
import { inspect } from 'node:util';

try {
  JSON.parse('{oops');
} catch (cause) {
  const err = new Error('設定ファイルを読めなかった', { cause });
  err.cause;                      // => SyntaxError: Expected property name ...
  console.log(inspect(err));      // => stack のあとに [cause]: SyntaxError: ... が入れ子で表示される
  JSON.stringify(err);            // => '{}'（message も cause も出ない）
}
```

## Contract

- `cause` には任意の値を渡せる（`Error` でなくても、文字列でも）。型は `unknown`
- `options.cause` を渡したときだけ `cause` プロパティが作られる。`{ cause: undefined }` でも作られる（値は `undefined`）。渡さなければ `'cause' in err` は `false`
- `cause` は列挙されないプロパティなので `Object.keys` / `JSON.stringify` / スプレッドに現れない。`message` / `stack` も同様
- 根本原因は `while (err instanceof Error && err.cause instanceof Error) err = err.cause` で辿る。`cause` が `Error` 以外の値でも止まるようにする
- `util.inspect`（`console.log` / `console.error`）は `[cause]:` を入れ子でインデント表示する。Node のクラッシュ時の表示も同じ
- `Error` のサブクラス（`TypeError` / `RangeError` / 自作クラス）でも同じ `options` 引数が使える

## Alternatives

- 文脈だけ足して同じエラーを投げ直したいなら `err.message = \`...: ${err.message}\`` でなく、必ず新しいエラーで包む（元の `stack` を壊さない）
- 複数の原因（並列処理で複数失敗）をまとめるなら `AggregateError`（カード error-aggregate）
- ログに出す形に展開するのはカード log-structured

## Pitfalls

- `JSON.stringify(err)` は `{}` になり `cause` も消える。API 応答やログに出すなら `name` / `message` / `cause` を明示的に展開し、`cause` は再帰的に処理する
- `cause` を自分自身にすると辿るループが止まらない。深さの上限を付ける
- `throw new Error('failed: ' + err.message)` は原因の `stack` と型を捨てる。`{ cause: err }` を付ける
- `cause` は `unknown` なので `err.cause.message` は型エラー。`instanceof Error` で絞ってから使う
- ES2022 未満の `lib` 設定では `ErrorOptions` 型が無く `new Error(msg, { cause })` がコンパイルエラーになる。実行時（Node 16.9+）は動く

## Test

`examples/error-cause-chain.test.ts`
