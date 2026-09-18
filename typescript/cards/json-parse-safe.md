---
id: json-parse-safe
lang: typescript
title: JSON 文字列を例外を投げずに解析する
tags: [JSON 解析, 例外を値に, 安全なパース, parse, json, attempt, safe-parse]
lib: es-toolkit
fn: attempt
since: "1.52.0"
verified: 2026-09-17
status: public
---

`JSON.parse` を `attempt` で包み、失敗を `[SyntaxError, null]` のタプルで受け取る。結果は `unknown` なので、形が必要ならスキーマ検証（zod）につなぐ。

## Signature

```ts
function attempt<T, E = unknown>(func: () => T): [null, T] | [E, null]  // attempt<unknown, SyntaxError>(() => JSON.parse(text))
```

## Usage

```ts
import { attempt } from 'es-toolkit';
import { z } from 'zod';

const [err, raw] = attempt<unknown, SyntaxError>(() => JSON.parse('{"name":"alice"}'));
// => err: null, raw: { name: 'alice' }（型は unknown）
const [err2] = attempt<unknown, SyntaxError>(() => JSON.parse('{oops'));
// => err2: SyntaxError("Expected property name or '}' in JSON at position 1 ...")
z.object({ name: z.string() }).safeParse(raw);
// => { success: true, data: { name: 'alice' } }（unknown から型付きへ）
```

## Contract

- 解析できれば `[null, 値]`、`JSON.parse` が投げた `SyntaxError` は `[SyntaxError, null]` として返る。例外は伝播しない
- `JSON.parse` の戻り値は `any` なので、型引数 `attempt<unknown, SyntaxError>` で `unknown` に固定する。値の形は zod などで別途検証する
- 失敗する入力: `''`、`'undefined'`、`'{a:1}'`（引用符なしキー）、`'{"a":1,}'`（末尾カンマ）、`'NaN'`、シングルクォート文字列
- 成功するが注意が要る入力: `'1e400'` → `Infinity`、`'12345678901234567890'` → `12345678901234567000`（精度落ち）、`'9007199254740993'` → `9007199254740992`。トップレベルの `null` / 数値 / 文字列も正当な JSON
- `"__proto__"` キーは解析結果の自身のプロパティになり、プロトタイプは汚染されない。`z.object` に通すと除去される
- `JSON.parse(text, reviver)` の第 2 引数で値を変換できる（`'at'` キーを `new Date(v)` にするなど）。Node 21 以降は reviver の第 3 引数 `context.source` で元の文字列が取れ、大きな整数を `BigInt` にできる（TypeScript 5.9 の lib には第 3 引数の型が無いので reviver をキャストする）

## Alternatives

- 例外のままでよければ素の `JSON.parse` を `try/catch` で
- 解析と検証を一度にやるなら zod の `z.string().transform((s) => JSON.parse(s))`（失敗は `transform` 内の例外として伝播するので `attempt` と組み合わせる）
- 他ライブラリでは valibot / ajv（検証側）。ここでは名前のみ

## Pitfalls

- `JSON.parse(text) as User` は検証していない。形を信用できないデータには zod を通す
- `Object.assign({}, parsed)` は `"__proto__"` 自身のプロパティを setter として扱い、コピー先のプロトタイプを差し替える。スプレッド `{ ...parsed }` や `structuredClone` は自身のプロパティのまま複製する
- `attempt(() => JSON.parse(await res.text()))` のような非同期には使えない。`attemptAsync` か、先に `await` して文字列にしてから渡す
- 精度が必要な大きな整数は文字列として送ってもらうか、reviver の `context.source` で `BigInt` に変換する

## Test

`examples/json-parse-safe.test.ts`
