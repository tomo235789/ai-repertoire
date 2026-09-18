---
id: io-join-path
lang: python
title: パスを結合する
tags: [パス結合, ファイルパス, 正規化, 区切り文字, join-path, path, normalize, separator]
lib: stdlib
fn: pathlib.Path
since: "3.4"
verified: 2026-09-17
status: public
---

パスの断片を `/` 演算子で OS の区切り文字でつなぐ。`.` と重複した区切りは消えるが `..` は残る。ファイルの読み書き先を組み立てるときに使う。

## Signature

```python
Path("a") / "b"  # PurePath.joinpath(*pathsegments) と同じ（/ 演算子）
```

## Usage

```python
from pathlib import Path

Path("logs") / "app" / "x.log"           # => PosixPath('logs/app/x.log')
Path("logs/app") / "../db" / "x.sqlite"  # => PosixPath('logs/app/../db/x.sqlite')（.. は残る）
Path("/var") / "/log"                    # => PosixPath('/log')（絶対パスは後ろが勝つ）
Path("a") / "./b" / ""                   # => PosixPath('a/b')（. と空は消える）
(Path("logs/app") / "../db").resolve()   # => PosixPath('/cwd/logs/db')（絶対化して .. を解決）
str(Path("a") / "b")                     # => 'a/b'
```

## Contract

- 新しい `Path` を返す。元のオブジェクトは変わらない（`Path` は不変）
- 重複した区切りと `.` は消える（`Path("a//b")` も `Path("a") / "./b"` も `a/b`）。空文字列は無視される。**`..` は残る**（`(Path("logs/app") / "../db").parts` は `('logs', 'app', '..', 'db')`）
- 右辺が絶対パスならそれまでの部分は捨てられ、後ろが勝つ（`Path("/var") / "/log"` → `/log`、`Path("/a/b") / "/c" / "d"` → `/c/d`）。`os.path.join` も同じ
- 末尾の `/` は保持しない（`Path("a/") / "b/"` は `a/b`）。`Path("")` は `.`
- 右辺は `str`・`Path`・`os.PathLike`。`int` や `None` は `TypeError`。左辺が `str` で右辺が `Path` でもよい
- 区切りは実行 OS 依存。`PurePosixPath` は常に `/`、`PureWindowsPath` は常に `\` で、どの OS でも使える。`PurePosixPath("a") / "b\\c"` は `\` を区切りとみなさない（`parts` は `('a', 'b\\c')`）。`PureWindowsPath("C:/a") / "D:/b"` はドライブごと置き換わる
- ファイルシステムは見ない。`resolve()` はカレントディレクトリからの絶対パスにして `..` とシンボリックリンクを解決する。文字列のまま `..` を畳むなら `os.path.normpath`
- `str(p)` と `os.fspath(p)` はどちらも同じ文字列。`open()` や `subprocess` は `Path` をそのまま受ける

## Alternatives

- `os.path.join(a, b)` は文字列を返す。絶対パスで後ろが勝つ規則は同じだが、`.` や重複した `/` を正規化せず（`os.path.join("a//", "./b")` は `'a//./b'`）、末尾の空文字列で `'a/'` になる
- 複数まとめて渡すなら `Path("a", "b", "c")` か `Path("a").joinpath("b", "c")`
- 分解は `p.parent` / `p.name` / `p.suffix` / `p.stem`
- URL は `/` で組み立てない（`Path("https://x.com") / "a"` は `https:/x.com/a`）。カード url-join-path の `urljoin`

## Pitfalls

- TypeScript（Node）の `path.join('/a', '/b')` は `'/a/b'` だが、Python は `/b`。ユーザー入力を `base / user_input` すると絶対パスで `base` を丸ごと乗っ取れる
- `..` も残るので `base / "../etc/passwd"` は `base` の外を指す。`(base / user_input).resolve().is_relative_to(base.resolve())` で確認する
- Node の `join` は `..` を畳むが Python は畳まない。比較や表示で正規化したいなら `resolve()`（絶対化する）か `os.path.normpath`（文字列のまま）
- `Path` は末尾の `/` を落とす。「ディレクトリである」ことを末尾の `/` で表す文字列 API（`rsync` など）に渡すときは自分で足す

## Test

`examples/io-join-path_test.py`
