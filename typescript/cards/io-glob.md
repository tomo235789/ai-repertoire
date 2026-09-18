---
id: io-glob
lang: typescript
title: パターンに合うファイルを列挙する
tags: [ファイル列挙, ワイルドカード, 再帰検索, ディレクトリ走査, glob, find-files, wildcard, list-files]
lib: stdlib
fn: glob
since: "Node 22"
verified: 2026-09-17
status: public
---

`**/*.ts` のようなパターンに合うパスをディレクトリを再帰的に辿って列挙する。ビルド対象の収集や一括処理の対象探しに使う。

## Signature

```ts
function glob(pattern: string | readonly string[], options?: GlobOptions): AsyncIterator<string | Dirent>
```

## Usage

```ts
import { glob } from 'node:fs/promises';

const cwd = '/path/to/project';
for await (const p of glob('**/*.ts', { cwd, exclude: ['node_modules/**'] })) {
  console.log(p); // cwd からの相対パス: 'src/a.ts', 'src/sub/b.ts', ...（順序は不定）
}
const found = await Array.fromAsync(glob(['**/*.ts', '**/*.js'], { cwd }));
```

## Contract

- `AsyncIterator` を返し、`cwd`（既定 `process.cwd()`）からの相対パスを `/` 区切りで yield する。パターンが絶対パスなら絶対パスを yield する
- 順序は保証されない（深さ順でも辞書順でもない）。並びが要るなら集めて `sort` する
- `exclude` は関数か glob パターンの配列。関数には相対パスが渡され、ディレクトリで `true` を返すとその中を辿らない（`node_modules` を丸ごと飛ばせる）
- `withFileTypes: true` にすると `Dirent` を yield する。`dirent.name` と `dirent.parentPath` から `join` でフルパスを作る
- `**` はディレクトリにもマッチする（`src/*` は `src/sub` を含む）。ファイルだけが欲しければ `withFileTypes` で `isFile()` を見るか、拡張子で絞る
- 何にもマッチしなければ 1 つも yield せず、例外にならない。パターンは配列で複数渡せる

## Alternatives

- 1 階層だけなら `readdir(dir, { withFileTypes: true })` で十分
- 全ファイルを再帰的に取るなら `readdir(dir, { recursive: true })`（Node 20+）
- ブレース展開 `{a,b}` や `!` の否定パターンが要るなら `tinyglobby` か `fast-glob`

## Pitfalls

- `exclude` に `'!foo'` のような否定パターンは書けない（公式ドキュメントに明記）
- `exclude` の glob パターン配列は Node 22.14 / 23.7 から。それより前は関数だけ。`fs.glob` 自体は Node 22.17 / 24.0 で安定版になった
- `cwd` を省くと `process.cwd()` から探し始めるので、テストや CLI では実行場所で結果が変わる。`cwd` は明示する
- `for await` を途中で `break` しても残りのディレクトリ走査が即座に止まる保証はない。大きなツリーでは `exclude` で先に絞る

## Test

`examples/io-glob.test.ts`
