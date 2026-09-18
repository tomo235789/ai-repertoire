---
id: io-read-lines
lang: python
title: ファイルを 1 行ずつ読む
tags: [行読み, ストリーム, 逐次処理, 大きなファイル, read-lines, readline, stream, line-by-line]
lib: stdlib
fn: open
since: "3.0"
verified: 2026-09-17
status: public
---

ファイルをメモリに全部載せずに 1 行ずつ取り出す。ログの走査や巨大な CSV・JSONL の逐次処理に使う。

## Signature

```python
open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None)
```

## Usage

```python
with open("app.log", encoding="utf-8") as f:
    for line in f:
        print(line.rstrip("\n"))  # 行末の改行を除いた 1 行
# 'a\nb\n' なら 'a\n', 'b\n' の 2 回。'a\r\nb' でも 'a\n', 'b'
```

## Contract

- `for line in f` は 1 行ずつ文字列を返す。**行末の改行 `\n` は残る**（最終行に改行が無ければその行だけ無い）。`rstrip("\n")` で落とす（`rstrip()` だと末尾の空白も消える）
- `newline=None`（既定）は universal newlines: `\r\n` も単独の `\r` も `\n` に変換して返す。`newline=""` にすると変換せず `'a\r\n'` のまま。`f.newlines` で実際に現れた改行種別が分かる
- ファイル末尾の改行 1 つは「最後の空行」にならない（`'a\nb\n'` も `'a\nb'` も 2 行）。`'a\n\n'` は `['a\n', '\n']`、空ファイルは 0 行、`'\n'` だけなら `['\n']`
- 遅延読み込み。先頭 1 行を取り出した時点で読んでいるのはバッファ 1 つ分だけで、ファイル全体はメモリに載らない
- 反復は消費的。`break` した後は続きから読めるが、最後まで読んだ後は空。反復中の `f.tell()` は `OSError`
- 存在しなければ `FileNotFoundError`、ディレクトリなら `IsADirectoryError`。`encoding` に合わないバイト列は **その行ではなく、それを含むバッファを読んだ時点で** `UnicodeDecodeError`（小さいファイルでは 1 行も取り出せずに出る）。`errors="replace"` で U+FFFD に置換して読み続ける
- `with` を抜けるとファイルは閉じられ、以降の反復は `ValueError`
- `encoding` を省くとロケール依存（Windows では cp932 など）。`utf-8-sig` なら先頭の BOM を除く（`utf-8` は `'\ufeff'` として最初の行に残る）

## Alternatives

- 小さいファイルなら `Path(p).read_text(encoding="utf-8").splitlines()`。全体をメモリに載せるが、改行を含まず `\r\n` も扱え、末尾の改行で空要素は増えない
- `f.readlines()` は改行付きのリストとしてすべて読み込む。`for line in f` があれば要らない
- バイナリのまま行で区切るなら `open(p, "rb")`。`b'\n'` だけが区切りで `\r` は残る
- CSV は `csv.reader(f)`（`newline=""` で開く）、JSONL は各行を `json.loads`

## Pitfalls

- TypeScript（Node）の `readline` は改行を落とすが、Python の `for line in f` は残す。`if line == "a"` は `"a\n"` と一致しない
- `encoding` を省かない。ロケール依存で環境ごとに結果が変わる（`-X warn_default_encoding` で `EncodingWarning`）
- `f.read().split("\n")` は末尾の改行で最後に `''` が 1 つ増える。分割するなら `splitlines()`
- 空行の扱い（読み飛ばすか）と `strip()` の範囲（改行だけか空白も含むか）を決めておく。`line.strip()` は先頭の空白も消す

## Test

`examples/io-read-lines_test.py`
