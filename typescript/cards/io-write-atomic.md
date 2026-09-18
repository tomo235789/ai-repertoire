---
id: io-write-atomic
lang: typescript
title: ファイルを原子的に書き換える
tags: [原子的書き込み, 安全な保存, 一時ファイル, 置き換え, atomic-write, rename, replace, safe-save]
lib: stdlib
fn: rename
since: "Node 18"
verified: 2026-09-17
status: public
---

同じディレクトリの一時ファイルに全部書いてから `rename` で本来の名前に置き換える。設定ファイルやキャッシュの保存で、途中まで書かれた壊れたファイルを読まれないようにする。

## Signature

```ts
function rename(oldPath: PathLike, newPath: PathLike): Promise<void>
```

## Usage

```ts
import { rename, writeFile } from 'node:fs/promises';

const target = 'config.json';
const tmp = `${target}.${process.pid}.tmp`; // 同じディレクトリに置く
await writeFile(tmp, JSON.stringify({ ok: true }));
await rename(tmp, target); // 既存の config.json を丸ごと置き換える
// => 読む側は「古い内容」か「新しい内容」のどちらかしか見ない
```

## Contract

- `newPath` が既にあれば上書きする。置き換え後の `newPath` は一時ファイルの inode になり、旧ファイルは消える
- 同じファイルシステム内では、書き換え中に読んだ側が途中状態を見ることはない（古い内容か新しい内容のどちらか）
- 別のデバイス（別のマウント）へは `EXDEV` で失敗する。一時ファイルは必ず同じディレクトリに作る
- `rename` が失敗しても `newPath` は変わらず、一時ファイルは残る。`oldPath` が無ければ `ENOENT`、`newPath` がディレクトリなら `EISDIR`、`newPath` の親ディレクトリが無ければ `ENOENT`
- パーミッションは一時ファイルのものになる。旧ファイルの `0600` は引き継がれない（`writeFile` の既定は `0644` から umask を引いた値）
- 成功時は `undefined` で resolve する

## Alternatives

- `writeFile(target, data)` を直接呼ぶと、書き込み途中でプロセスが落ちたときや、同時に読まれたときに途中までの内容が見える
- 電源断まで耐えたいなら `open(tmp, 'w')` した `FileHandle` に書いて `await fh.sync()` してから `rename` する。`rename` 自体は `fsync` しない
- 同じ意味論のパッケージ: `write-file-atomic`（一時ファイル名の生成・パーミッションの引き継ぎまで面倒を見る）

## Pitfalls

- `os.tmpdir()` に一時ファイルを作ると、保存先が別のデバイスのときに `EXDEV` になる。`dirname(target)` の中に作る
- 途中で例外が出たときの一時ファイルは自分で `rm(tmp, { force: true })` する。放置すると `.tmp` が溜まる
- 複数プロセスが同じ `target` を書くなら一時ファイル名に `process.pid` や乱数を入れる。名前が衝突すると互いの内容を混ぜる
- Python の `os.replace` と同じ意味論。`os.rename` は Windows で既存ファイルがあると失敗する

## Test

`examples/io-write-atomic.test.ts`
