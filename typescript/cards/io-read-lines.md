---
id: io-read-lines
lang: typescript
title: ファイルを 1 行ずつ読む
tags: [行読み, ストリーム, 逐次処理, 大きなファイル, read-lines, readline, stream, line-by-line]
lib: stdlib
fn: createInterface
since: "Node 18"
verified: 2026-09-17
status: public
---

ファイルをメモリに全部載せずに 1 行ずつ取り出す。ログの走査や巨大な CSV・JSONL の逐次処理に使う。

## Signature

```ts
function createInterface(options: ReadLineOptions): Interface // { input: ReadableStream; crlfDelay?: number; ... }
```

## Usage

```ts
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';

const rl = createInterface({ input: createReadStream('app.log'), crlfDelay: Infinity });
for await (const line of rl) {
  console.log(line); // 改行を含まない 1 行。'a\nb\n' なら 'a', 'b' の 2 回
}
```

## Contract

- `for await` は行を文字列で 1 つずつ yield する。`\n`・`\r\n`・単独の `\r` のどれも行区切りとして扱い、行末の改行文字は含まれない
- ファイル末尾の改行 1 つは「最後の空行」にならない（`'a\nb\n'` も `'a\nb'` も `['a', 'b']`）。`'a\n\n'` は `['a', '']`、空ファイルは 0 行、`'\n'` だけなら `['']`
- `crlfDelay: Infinity` を付けると `\r` と `\n` が別チャンクで届いても常に 1 つの改行として扱う。既定（100ms）では届く間隔が開くと空行が 1 つ増える
- ループを `break` しても `close` イベントは出ず、入力ストリームも破棄されない（Node 26 で確認）。途中で止めるなら `finally` で `rl.close()` と `stream.destroy()` を自分で呼ぶ。呼ばないとファイル記述子が開いたまま残る
- 入力ストリームのエラー（存在しないファイルの `ENOENT` など）は `for await` の例外として投げられる
- `input` は `Readable` なら何でもよい（`process.stdin`、`Readable.from([...])` も可）

## Alternatives

- 小さいファイルなら `(await readFile(path, 'utf8')).split('\n')`。全体をメモリに載せるうえ、末尾の改行で最後に `''` が 1 つ増え、`\r\n` の `\r` も残る
- `node:readline/promises` の `createInterface` は対話入力（`rl.question`）向け。行の反復だけならどちらでも同じ
- 速度が要るなら `rl.on('line', ...)` のイベント API（公式ドキュメントが `for await` より速いと明記）

## Pitfalls

- `for await` を `break` で抜けるときは `finally` で `stream.destroy()` を呼ぶ。呼ばないとファイル記述子が残り、多数のファイルを途中まで読む処理で枯渇する

- `crlfDelay: Infinity` を忘れると、`\r\n` のファイルで `\r` と `\n` がチャンク境界に跨ったときだけ空行が混じる。再現しにくいので常に付ける
- 行は文字列で来るので、`JSON.parse` や `Number` への変換は自分で行う。空行の扱い（読み飛ばすか）も決めておく
- Python の `for line in f` は改行を残す（`'a\n'`）が、readline は改行を落とす。`rstrip()` 相当は不要

## Test

`examples/io-read-lines.test.ts`
