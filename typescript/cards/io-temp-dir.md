---
id: io-temp-dir
lang: typescript
title: 一時ディレクトリを作る
tags: [一時ディレクトリ, 作業領域, テスト用, 後始末, temp-dir, tmpdir, mkdtemp, scratch]
lib: stdlib
fn: mkdtemp
since: "Node 18"
verified: 2026-09-17
status: public
---

他と衝突しない名前の一時ディレクトリを作る。テストの作業領域や、加工途中のファイル置き場に使う。

## Signature

```ts
function mkdtemp(prefix: string, options?: ObjectEncodingOptions | BufferEncoding | null): Promise<string>
```

## Usage

```ts
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dir = await mkdtemp(join(tmpdir(), 'myapp-')); // => '/var/folders/.../T/myapp-wtaL8o'
try {
  // dir の中で作業する
} finally {
  await rm(dir, { recursive: true, force: true }); // 中身ごと消す
}
```

## Contract

- `prefix` の直後にランダムな 6 文字を付けた名前でディレクトリを作り、そのパスで resolve する。区切りは足さないので、`prefix` の末尾を `-` などで終えておく
- 呼ぶたびに別のディレクトリになる。作成は `mkdtemp(3)` に任せるので、同時に呼んでも衝突しない
- パーミッションは `0700`（所有者だけ読み書きできる）
- `prefix` の親ディレクトリが無ければ `ENOENT`。親は作らない
- `os.tmpdir()` は OS の一時領域（macOS では `/var/folders/...`、Linux では `/tmp`、`TMPDIR` 環境変数で変わる）を末尾の区切りなしで返す

## Alternatives

- 一時ファイルを 1 つだけ作る stdlib 関数は無い。`mkdtemp` で作ったディレクトリの中に固定名で置く
- 後始末を自動化したいなら `tmp` パッケージ（プロセス終了時に消せる）
- 削除は `rm(dir, { recursive: true, force: true })`。`force` を付けないと既に無いときに `ENOENT`

## Pitfalls

- `mkdtemp('/tmp/myapp-')` のように区切りを固定で書くと Windows で壊れる。`join(tmpdir(), 'myapp-')` にする
- `prefix` の末尾に `X` を並べない（BSD 系ではランダム文字に置き換えられる、と公式ドキュメントが注意している）
- vitest では `beforeEach` で作って `afterEach` で消す。テストが失敗しても消えるように、`try/finally` ではなくフックに書く
- Python の `tempfile.TemporaryDirectory()` はコンテキストマネージャで自動削除するが、Node は自分で `rm` する

## Test

`examples/io-temp-dir.test.ts`
