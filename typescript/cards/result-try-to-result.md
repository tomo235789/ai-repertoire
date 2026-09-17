---
id: result-try-to-result
lang: typescript
title: 例外を投げる関数の結果をタプルで受け取る
tags: [例外を値に, エラーハンドリング, タプル, 結果型, attempt, try-catch, result-tuple]
lib: es-toolkit
fn: attempt
since: "1.52.0"
verified: 2026-09-17
status: public
---

例外を投げるかもしれない同期関数を実行し、`[error, null]` か `[null, result]` のタプルで返す。`try/catch` のネストを避けて分岐を平らにするのに使う。

## Signature

```ts
function attempt<T, E = unknown>(func: () => T): [null, T] | [E, null]
```

## Usage

```ts
import { attempt } from 'es-toolkit';

const [err, parsed] = attempt(() => JSON.parse('{"ok":true}'));
// => err: null, parsed: { ok: true }
const [err2, parsed2] = attempt(() => JSON.parse('{oops'));
// => err2: SyntaxError, parsed2: null
if (err2 === null) console.log(parsed2); // 失敗側は [E, null] で E に null を含み得るため、型は自動では絞り込まれない
```

## Contract

- `func` を即座に 1 回呼ぶ。正常に返れば `[null, 戻り値]`、例外を投げれば `[投げられた値, null]` を返す
- 例外は `Error` に限らず投げられた値をそのまま返す（文字列や `undefined` も）
- `func` が `undefined` を返した場合は `[null, undefined]`。エラー側は `null` なので区別できる
- `Promise` を返す関数を渡すと `[null, Promise]` が返り、reject は捕捉されない。非同期には `attemptAsync` を使う
- エラーの型 `E` は既定で `unknown`。`attempt<T, SyntaxError>` のように明示できるが実行時の検証はしない

## Alternatives

- 非同期関数は `attemptAsync(async () => ...)`（`Promise<[null, T] | [E, null]>` を返す）
- 依存を増やせない場合は `try { return [null, fn()] } catch (e) { return [e, null] }`
- エラーを値として引き回すなら `neverthrow` の `Result` 型（`map` / `andThen` で連鎖できる）

## Pitfalls

- 判定は `err === null` で行う。`if (!err)` は `func` が `0` や `''` を投げた場合に誤判定する（投げる側の問題だが、外部コードでは起こり得る）
- `attempt(() => fetch(...))` のように `Promise` を返すと例外が捕まらない。`attemptAsync` に置き換える
- `E` に型を付けても `catch` と同じで型は保証されない。`instanceof` で確認してから使う
- 成功側の `T` を `null` 許容にすると `[null, null]` が成功か失敗か分からなくなる。判定は必ずエラー側で行う
- `throw null` された場合も `[null, null]` になり、投げられた値は正規化されないので成功と区別できない。`null` を投げる外部コードには使えない

## Test

`examples/result-try-to-result.test.ts`
