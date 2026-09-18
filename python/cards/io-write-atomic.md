---
id: io-write-atomic
lang: python
title: ファイルを原子的に書き換える
tags: [原子的書き込み, 安全な保存, 一時ファイル, 置き換え, atomic-write, rename, replace, safe-save]
lib: stdlib
fn: os.replace
since: "3.3"
verified: 2026-09-17
status: public
---

同じディレクトリの一時ファイルに全部書いてから `os.replace` で本来の名前に置き換える。設定ファイルやキャッシュの保存で、途中まで書かれた壊れたファイルを読まれないようにする。

## Signature

```python
os.replace(src, dst, *, src_dir_fd=None, dst_dir_fd=None)
```

## Usage

```python
import os, tempfile
target = "config.json"
with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(target) or ".", delete=False, encoding="utf-8") as tmp:
    tmp.write('{"ok": true}')
    tmp.flush(); os.fsync(tmp.fileno())  # 電源断まで耐えたいなら（replace 自体は fsync しない）
try:
    os.replace(tmp.name, target)  # 既存の config.json を丸ごと置き換える
except BaseException:
    os.unlink(tmp.name); raise  # 失敗しても一時ファイルを残さない
# => 読む側は「古い内容」か「新しい内容」のどちらかしか見ない
```

## Contract

- `dst` が既にあれば黙って上書きする。置き換え後の `dst` は一時ファイルの inode になり（`st_ino` が一致）、旧ファイルは消える。`src` は無くなる。返り値は `None`
- 同じファイルシステム内では原子的（POSIX の `rename(2)`）。書き換え中に読む側が途中状態を見ることはなく、置き換え前から開いていたファイルオブジェクトは旧内容を読み続ける
- 別のデバイス（別のマウント）へは `OSError`（`errno.EXDEV`）。一時ファイルは必ず `dst` と同じディレクトリに作る
- 失敗しても `dst` は変わらず、一時ファイルは残る。`src` が無ければ `FileNotFoundError`、`dst` がディレクトリなら `IsADirectoryError`、`dst` の親が無ければ `FileNotFoundError`、`src` がディレクトリで `dst` がファイルなら `NotADirectoryError`、空でないディレクトリへは `OSError`（`ENOTEMPTY`）
- パーミッションは一時ファイルのものになる。`NamedTemporaryFile` / `mkstemp` は `0600` で作るので、`0644` だった `dst` は置き換え後 `0600` になる。引き継ぐなら `shutil.copymode(dst, tmp.name)` を先に
- `NamedTemporaryFile(delete=False)` は `with` を抜けても消えない（閉じるだけ）。書いている途中で例外が出ると一時ファイルが残り、`dst` は旧内容のまま
- `os.rename` は POSIX では同じ動きだが、Windows では `dst` があると失敗する（公式ドキュメント）。クロスプラットフォームでは `os.replace` を使う

## Alternatives

- `Path.write_text` を直接呼ぶと、書き込み途中でプロセスが落ちたときや同時に読まれたときに途中までの内容が見える
- `tempfile.mkstemp(dir=...)` でファイル記述子を受けて `os.fdopen` する低水準版（名前を自分で組み立てると、同じプロセス内の同時書き込みや残骸ファイルと衝突するので使わない）
- ディレクトリのエントリまで永続化したいなら、置き換え後に親ディレクトリを `os.open(dir, os.O_RDONLY)` して `os.fsync`（POSIX）

## Pitfalls

- TypeScript（Node）の `fs.rename` と同じ意味論。Python では `os.rename` ではなく `os.replace` を使う（Windows で `dst` があると `os.rename` は失敗する）
- `tempfile.gettempdir()` に一時ファイルを作ると、保存先が別デバイスのとき `EXDEV`。`dir=` に `dst` の親ディレクトリを渡す
- 例外時の一時ファイルは自分で消す（`try/except` で `os.unlink(tmp.name)`）。放置すると `tmp*` が溜まる
- `NamedTemporaryFile` は `0600`。他ユーザーにも読ませるファイルなら置き換え前に `os.chmod(tmp.name, 0o644)`
- `tmp.write()` の後に `flush()` せず `os.fsync(tmp.fileno())` すると Python 側のバッファが書かれていない。`flush()` → `fsync()` の順

## Test

`examples/io-write-atomic_test.py`
