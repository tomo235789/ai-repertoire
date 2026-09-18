---
id: io-temp-dir
lang: python
title: 一時ディレクトリを作る
tags: [一時ディレクトリ, 作業領域, テスト用, 後始末, temp-dir, tmpdir, mkdtemp, scratch]
lib: stdlib
fn: tempfile.TemporaryDirectory
since: "3.2"
verified: 2026-09-17
status: public
---

他と衝突しない名前の一時ディレクトリを作り、`with` を抜けるときに中身ごと消す。テストの作業領域や、加工途中のファイル置き場に使う。

## Signature

```python
tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False, *, delete=True)  # ignore_cleanup_errors は 3.10、delete は 3.12 以降
```

## Usage

```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="myapp-") as d:
    print(d)  # => '/var/folders/.../T/myapp-nx9o7_iz'（str）
    (Path(d) / "work.txt").write_text("x", encoding="utf-8")
# with を抜けると中身ごと消える

d = tempfile.mkdtemp(prefix="myapp-")  # 自動では消えない。shutil.rmtree(d) で消す
```

## Contract

- `with` の値はパスの `str`（`Path` ではない）。`.name` でも同じ。絶対パス
- `with` を抜けると中身ごと削除される（例外で抜けても）。読み取り専用のファイル・ディレクトリが中にあっても権限を戻して消す。`ignore_cleanup_errors=True`（3.10 以降）は削除に失敗しても例外にしない（公式ドキュメント。POSIX では読み取り専用の中身も既定で消せる）
- パーミッションは `0700`（所有者だけ）。`mkdtemp` も同じ
- 名前は `prefix` + ランダム 8 文字 + `suffix`。`prefix` の既定は `tmp`。区切りは足さないので `prefix` の末尾を `-` などで終える。呼ぶたびに別の名前になる
- `dir` の既定は `tempfile.gettempdir()`（`TMPDIR` 環境変数、macOS では `/var/folders/.../T`、Linux では `/tmp`）。`dir` は `Path` も可。親が無ければ `FileNotFoundError`（作らない）
- `cleanup()` で明示的に消せ、2 回呼んでも安全。`delete=False`（3.12 以降）で `with` を抜けても残る
- `mkdtemp()` は `str` を返し、削除しない
- オブジェクトへの参照が無くなると GC 時に削除され `ResourceWarning`（`Implicitly cleaning up`）が出る

## Alternatives

- 一時ファイル 1 つは `tempfile.NamedTemporaryFile()`（`with` で自動削除）か `mkstemp()`
- pytest なら `tmp_path` フィクスチャ（`Path`。テストごとに別で、失敗時に中身を確認できる）
- 手動の削除は `shutil.rmtree(d, ignore_errors=True)`
- `Path` として扱うなら `Path(d)`。`Path(tempfile.mkdtemp())`

## Pitfalls

- TypeScript（Node）の `mkdtemp` は自分で `rm` するが、Python は `with` で自動削除。`mkdtemp` を使うなら `try/finally` で `shutil.rmtree`
- `with` の値は `str`。`/` で結合したいなら `Path(d)` に包む
- `with` ブロックの外にパスを持ち出しても既に消えている。関数の返り値にするなら `delete=False` か `mkdtemp`
- `dir="/tmp"` のように固定で書くと Windows で壊れる。`dir` を省けば OS ごとの一時領域になる
- ファイルを開いたまま `with` を抜けると Windows では削除に失敗する（公式ドキュメント）。閉じてから抜ける

## Test

`examples/io-temp-dir_test.py`
