"""io-temp-dir: tempfile.TemporaryDirectory / mkdtemp の Contract を検証する。"""

import gc
import os
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

import pytest


def test_returns_str_and_removes_on_exit(tmp_path: Path) -> None:
    """with の値はパスの str で、抜けると中身ごと消える。"""
    with tempfile.TemporaryDirectory(dir=tmp_path) as d:
        assert isinstance(d, str) and os.path.isabs(d)
        assert os.path.isdir(d)
        (Path(d) / "sub").mkdir()
        (Path(d) / "sub" / "f.txt").write_text("x", encoding="utf-8")
    assert not os.path.exists(d)


def test_removes_on_exception(tmp_path: Path) -> None:
    """例外で抜けても削除される。"""
    with pytest.raises(RuntimeError):
        with tempfile.TemporaryDirectory(dir=tmp_path) as d:
            raise RuntimeError("boom")
    assert not os.path.exists(d)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX のパーミッション")
def test_permission_is_0700(tmp_path: Path) -> None:
    """パーミッションは 0700。mkdtemp も同じ。"""
    with tempfile.TemporaryDirectory(dir=tmp_path) as d:
        assert os.stat(d).st_mode & 0o777 == 0o700
    m = tempfile.mkdtemp(dir=tmp_path)
    assert os.stat(m).st_mode & 0o777 == 0o700


def test_prefix_suffix_and_dir(tmp_path: Path) -> None:
    """名前は prefix + ランダム 8 文字 + suffix。dir は Path でもよく、その直下に作る。"""
    with tempfile.TemporaryDirectory(prefix="myapp-", suffix="-x", dir=tmp_path) as d:
        name = Path(d).name
        assert name.startswith("myapp-") and name.endswith("-x")
        assert len(name) == len("myapp-") + 8 + len("-x")
        assert Path(d).parent == tmp_path
    with tempfile.TemporaryDirectory(dir=tmp_path) as d:
        assert Path(d).name.startswith("tmp")


def test_missing_parent_raises(tmp_path: Path) -> None:
    """dir の親が無ければ FileNotFoundError。作らない。"""
    with pytest.raises(FileNotFoundError):
        tempfile.TemporaryDirectory(dir=tmp_path / "nope")
    assert not (tmp_path / "nope").exists()


def test_mkdtemp_persists_and_is_unique(tmp_path: Path) -> None:
    """mkdtemp は str を返し、自動では消えない。呼ぶたびに別の名前。"""
    names = {tempfile.mkdtemp(dir=tmp_path) for _ in range(5)}
    assert len(names) == 5
    for n in names:
        assert isinstance(n, str) and os.path.isdir(n)
        shutil.rmtree(n)
        assert not os.path.exists(n)


def test_cleanup_is_idempotent_and_delete_false(tmp_path: Path) -> None:
    """cleanup() は 2 回呼んでも安全。delete=False なら with を抜けても残る。"""
    t = tempfile.TemporaryDirectory(dir=tmp_path)
    assert os.path.isdir(t.name)
    t.cleanup()
    t.cleanup()
    assert not os.path.exists(t.name)
    with tempfile.TemporaryDirectory(dir=tmp_path, delete=False) as d:
        pass
    assert os.path.isdir(d)
    os.rmdir(d)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX のパーミッション")
def test_readonly_contents_are_removed(tmp_path: Path) -> None:
    """読み取り専用のファイル・ディレクトリが中にあっても消せる。"""
    with tempfile.TemporaryDirectory(dir=tmp_path) as d:
        sub = Path(d) / "ro"
        sub.mkdir()
        (sub / "f.txt").write_text("x", encoding="utf-8")
        os.chmod(sub / "f.txt", 0o400)
        os.chmod(sub, 0o500)
    assert not os.path.exists(d)


def test_gc_cleanup_emits_resource_warning(tmp_path: Path) -> None:
    """参照が無くなると GC 時に削除され ResourceWarning が出る。"""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t = tempfile.TemporaryDirectory(dir=tmp_path)
        name = t.name
        del t
        gc.collect()
    assert any(w.category is ResourceWarning for w in caught)
    assert not os.path.exists(name)


def test_gettempdir_is_default_and_honors_tmpdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """dir 省略時は gettempdir()。TMPDIR 環境変数で変わる。"""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    assert Path(tempfile.gettempdir()) == tmp_path
    with tempfile.TemporaryDirectory() as d:
        assert Path(d).parent == tmp_path
