"""io-write-atomic: 一時ファイル + os.replace の Contract を検証する。"""

import errno
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest


def write_atomic(target: Path, data: str) -> str:
    """カードの Usage と同じ手順。一時ファイル名を返す。"""
    with tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False, encoding="utf-8") as tmp:
        tmp_name = tmp.name
        try:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
    try:
        os.replace(tmp_name, target)
    except BaseException:
        # replace に失敗したら一時ファイルを残さない（別デバイスの EXDEV など）
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return tmp_name


def test_replaces_existing_file_and_removes_tmp(tmp_path: Path) -> None:
    """既存ファイルを上書きし、一時ファイルは無くなり、dst は一時ファイルの inode になる。"""
    target = tmp_path / "config.json"
    target.write_text("old", encoding="utf-8")
    src = tmp_path / "src"
    src.write_text("new", encoding="utf-8")
    ino = os.stat(src).st_ino
    assert os.replace(src, target) is None
    assert target.read_text(encoding="utf-8") == "new"
    assert not src.exists()
    assert os.stat(target).st_ino == ino


def test_usage_idiom_creates_or_replaces(tmp_path: Path) -> None:
    """Usage の手順で新規作成も置き換えもでき、一時ファイルは残らない。"""
    target = tmp_path / "config.json"
    tmp1 = write_atomic(target, '{"n": 1}')
    tmp2 = write_atomic(target, '{"n": 2}')
    assert target.read_text(encoding="utf-8") == '{"n": 2}'
    assert not os.path.exists(tmp1) and not os.path.exists(tmp2)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["config.json"]


def test_reader_opened_before_replace_sees_old_content(tmp_path: Path) -> None:
    """置き換え前から開いていたファイルオブジェクトは旧内容を読み続ける。"""
    target = tmp_path / "t.txt"
    target.write_text("old", encoding="utf-8")
    with open(target, encoding="utf-8") as reader:
        write_atomic(target, "new")
        assert reader.read() == "old"
    assert target.read_text(encoding="utf-8") == "new"


def test_failure_during_write_leaves_target_and_tmp(tmp_path: Path) -> None:
    """書いている途中で例外が出ても dst は旧内容のままで、一時ファイルは残る。"""
    target = tmp_path / "t.txt"
    target.write_text("old", encoding="utf-8")
    with pytest.raises(RuntimeError):
        with tempfile.NamedTemporaryFile("w", dir=tmp_path, delete=False, encoding="utf-8") as tmp:
            tmp.write("par")
            raise RuntimeError("boom")
    assert target.read_text(encoding="utf-8") == "old"
    assert tmp.closed
    assert Path(tmp.name).read_text(encoding="utf-8") == "par"


def test_error_cases(tmp_path: Path) -> None:
    """src 無し・dst の親無しは FileNotFoundError、dst がディレクトリは IsADirectoryError など。"""
    f = tmp_path / "f"
    f.write_text("x", encoding="utf-8")
    d = tmp_path / "d"
    d.mkdir()
    with pytest.raises(FileNotFoundError):
        os.replace(tmp_path / "nope", f)
    with pytest.raises(FileNotFoundError):
        os.replace(f, tmp_path / "nodir" / "x")
    with pytest.raises(IsADirectoryError):
        os.replace(f, d)
    with pytest.raises(NotADirectoryError):
        os.replace(d, f)
    nonempty = tmp_path / "ne"
    nonempty.mkdir()
    (nonempty / "child").write_text("", encoding="utf-8")
    with pytest.raises(OSError) as info:
        os.replace(d, nonempty)
    assert info.value.errno in (errno.ENOTEMPTY, errno.EEXIST)
    assert f.read_text(encoding="utf-8") == "x"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX のパーミッション")
def test_permission_comes_from_tmp_file(tmp_path: Path) -> None:
    """パーミッションは一時ファイルの 0600 になる。copymode で引き継げる。"""
    target = tmp_path / "t.txt"
    target.write_text("old", encoding="utf-8")
    os.chmod(target, 0o644)
    write_atomic(target, "new")
    assert os.stat(target).st_mode & 0o777 == 0o600

    os.chmod(target, 0o644)
    with tempfile.NamedTemporaryFile("w", dir=tmp_path, delete=False, encoding="utf-8") as tmp:
        tmp.write("new2")
    shutil.copymode(target, tmp.name)
    os.replace(tmp.name, target)
    assert os.stat(target).st_mode & 0o777 == 0o644


def _other_device_dir(base: Path) -> Path | None:
    """base と st_dev が異なるディレクトリを探す（無ければ None）。"""
    dev = os.stat(base).st_dev
    for cand in ("/dev/shm", "/run", "/System/Volumes/VM"):
        try:
            if os.stat(cand).st_dev != dev:
                return Path(cand)
        except OSError:
            continue
    return None


def test_cross_device_raises_exdev(tmp_path: Path) -> None:
    """別デバイスへの置き換えは OSError（errno.EXDEV）。"""
    other = _other_device_dir(tmp_path)
    if other is None:
        pytest.skip("別デバイスのディレクトリが見つからない")
    src = tmp_path / "src"
    src.write_text("x", encoding="utf-8")
    with pytest.raises(OSError) as info:
        os.replace(src, other / f"ai-repertoire-{os.getpid()}.tmp")
    assert info.value.errno == errno.EXDEV
    assert src.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="Windows では os.rename が失敗する")
def test_os_rename_also_overwrites_on_posix(tmp_path: Path) -> None:
    """POSIX では os.rename も既存ファイルを上書きする（違いは Windows だけ）。"""
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.write_text("A", encoding="utf-8")
    b.write_text("B", encoding="utf-8")
    os.rename(a, b)
    assert b.read_text(encoding="utf-8") == "A"
