---
id: io-glob
lang: python
title: パターンに合うファイルを列挙する
tags: [ファイル列挙, ワイルドカード, 再帰検索, ディレクトリ走査, glob, find-files, wildcard, list-files]
lib: stdlib
fn: pathlib.Path.glob
since: "3.4"
verified: 2026-09-17
status: public
---

`**/*.py` のようなパターンに合うパスをディレクトリを再帰的に辿って列挙する。ビルド対象の収集や一括処理の対象探しに使う。

## Signature

```python
Path.glob(pattern, *, case_sensitive=None, recurse_symlinks=False)  # case_sensitive は 3.12、recurse_symlinks は 3.13 以降
```

## Usage

```python
from pathlib import Path

root = Path("/path/to/project")
for p in root.glob("**/*.py"):
    print(p)  # => /path/to/project/src/a.py ...（root を基点にした Path。順序は不定）
found = sorted(root.rglob("*.py"))  # rglob('*.py') は glob('**/*.py') と同じ
[p for p in root.glob("**/*.py") if "node_modules" not in p.parts]  # 除外は自分で
```

## Contract

- イテレータを返し、`Path` を yield する。基点の `Path` が絶対なら絶対パス、相対なら相対パス（`Path(".").glob("*.py")` は `a.py` で `./` は付かない）
- 順序は保証されない（深さ順でも辞書順でもない）。並びが要るなら `sorted()`
- `**` は 0 個以上のディレクトリにマッチして再帰する。`rglob(pattern)` は `glob("**/" + pattern)` と同じ。`glob.glob` と違って `recursive=True` は要らない
- 隠しファイル（`.` で始まる）にもマッチし、`.git` の中も辿る（`glob.glob` は既定で除く）
- ディレクトリにもマッチする（`*` は `src` も返す）。ファイルだけなら `p.is_file()` で絞る。パターン末尾が `/` ならディレクトリだけ（3.11 以降）
- `**` で終わるパターン（`glob("**")`、`glob("src/**")`）は 3.12 まではディレクトリだけ、3.13 以降はファイルも返す
- `**` の再帰中にシンボリックリンクのディレクトリは辿らない（3.13 以降 `recurse_symlinks=True` で辿る。`glob.glob` は辿る）
- `case_sensitive`（3.12 以降）の既定は OS 依存: POSIX（macOS を含む）では区別し、Windows では区別しない。`case_sensitive=False` で `*.py` が `a.PY` にも合う
- 何にもマッチしなくても、基点のディレクトリが無くても空。例外にならない。空パターンは `ValueError`、絶対パスのパターンは `NotImplementedError`
- `[ab]` の文字クラスは使える。`{a,b}` のブレース展開と `!` の否定は無い（そのままの文字として扱う）

## Alternatives

- 1 階層だけなら `Path.iterdir()`（全エントリ）
- 文字列で受けたいなら `glob.glob(pattern, root_dir=..., recursive=True)`。隠しファイルは `include_hidden=True`（3.11 以降）
- 大きな木で `node_modules` や `.git` を枝刈りするなら `os.walk` で `dirnames` を書き換える
- ブレース展開や否定パターンが要るなら `wcmatch`

## Pitfalls

- TypeScript（Node）の `fs.glob` は `exclude` で `node_modules` を丸ごと飛ばせるが、`Path.glob` に除外は無い。`**` は `node_modules` や `.git` の中も全部辿るので、後から `parts` で除いても走査時間は減らない
- `Path.glob` は隠しファイルを含み、`glob.glob` は含まない。同じパターンでも結果が違う
- `glob("**")` の結果は 3.12 と 3.13 で変わる。ファイルが欲しければ `**/*` と書く
- macOS の既定ファイルシステムは大文字小文字を区別しないが、`glob` のマッチは区別する。`*.py` は `a.PY` に合わない
- 相対の `Path(".")` を基点にすると実行場所で結果が変わる。基点は `Path(__file__).parent` などで明示する

## Test

`examples/io-glob_test.py`
