---
id: log-structured
lang: typescript
title: ログを 1 行 1 JSON で出力する
tags: [構造化ログ, JSON ログ, ログ出力, エラーのログ, structured-logging, json-lines, logger, ndjson]
lib: stdlib
fn: console.log + JSON.stringify
since: "ES2015"
verified: 2026-09-17
status: public
---

ログを `{ level, time, msg, ...fields }` の JSON 1 行として標準出力に書く。ログ基盤（CloudWatch / Datadog / Loki など）で検索・集計できる形にするために使う。

## Signature

```ts
function log(level: 'debug' | 'info' | 'warn' | 'error', msg: string, fields?: Record<string, unknown>): void
```

## Usage

```ts
const serializeError = (e: Error): Record<string, unknown> =>
  ({ name: e.name, message: e.message, stack: e.stack, ...(e.cause instanceof Error && { cause: serializeError(e.cause) }) });
const RESERVED = new Set(['level', 'time', 'msg']);  // 呼び出し側の値で上書きさせない
const log = (level: 'debug' | 'info' | 'warn' | 'error', msg: string, fields: Record<string, unknown> = {}) =>
  console.log(JSON.stringify({ level, time: new Date().toISOString(), msg,
    ...Object.fromEntries(Object.entries(fields).filter(([k]) => !RESERVED.has(k))) },
    (_k, v) => (v instanceof Error ? serializeError(v) : v)));
log('info', 'request completed', { method: 'GET', status: 200, durationMs: 12 });
// => {"level":"info","time":"2026-09-17T14:00:00.000Z","msg":"request completed","method":"GET","status":200,...}
log('error', 'request failed', { err: new Error('boom') });  // => err は name / message / stack に展開される
```

## Contract

- `console.log` は引数を文字列化して末尾に改行を付けて `stdout` に書く。`JSON.stringify` した文字列を渡せば 1 行 1 JSON になる。`msg` に改行が含まれても `\n` にエスケープされ行は崩れない
- `new Date().toISOString()` は常に UTC の `YYYY-MM-DDTHH:mm:ss.sssZ`。ローカル時刻にはならない
- `Error` は自身の列挙可能プロパティを持たないので、そのまま `JSON.stringify` すると `{}` になる。replacer か事前変換で `name` / `message` / `stack` / `cause` を展開する。`cause` は再帰する
- `JSON.stringify` は `undefined` / 関数 / `Symbol` の値を持つキーを **落とし**、`NaN` / `Infinity` は `null` に、`Date` は `toJSON()` で ISO 文字列にする。`Map` / `Set` は `{}` になる
- 循環参照があると `TypeError: Converting circular structure to JSON`、`BigInt` があると `TypeError: Do not know how to serialize a BigInt` を投げ、**ログ自体が失敗** する
- キーの順序は挿入順。`{ level, time, msg, ...extra }` の順に書けば固定キーが先頭に来る。`fields` から予約キー（`level` / `time` / `msg`）を落としてから展開するので、呼び出し側の値でメタデータが上書きされることはない

## Alternatives

- 本番では `pino`（高速・非同期書き出し・子ロガー・redact 内蔵）か `winston`（トランスポート豊富）。どちらも出力は同じ 1 行 1 JSON
- 循環参照や `BigInt` を安全に文字列化するなら `safe-stable-stringify`（キー順も安定する）
- 秘密情報をマスクしてから出すのはカード log-redact-secrets、リクエスト ID を自動で付けるのはカード log-correlation-id

## Pitfalls

- `console.log('msg', obj)` のように複数引数で渡すと `util.inspect` 形式（`{ level: 'info' }`）になり JSON ではなくなる。必ず 1 つの文字列にする
- `Error` を `fields` に直接入れて `{}` になるのが最も多い事故。replacer で `instanceof Error` を処理する
- 循環参照でログ関数が例外を投げると、エラー処理の中でさらに落ちる。`fields` は自分で作った平らなオブジェクトに限るか、`safe-stable-stringify` を使う
- `stack` は複数行で長い。`debug` 以外では `stack` を落とすなど、レベルで出し分ける
- `console.log` は同期書き出し（パイプ先によっては非同期）で、大量に出すとブロックする。高負荷なら `pino` を使う

## Test

`examples/log-structured.test.ts`
