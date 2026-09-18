"""io-glob: pathlib.Path.glob / rglob の Contract を検証する。"""

import glob
import os
import sys
from collections.abc import Iterable
from pathlib import Path

import pytest

FILES = ["a.py", "b.txt", "src/c.py", "src/sub/d.py", "src/.hidden.py", ".git/e.py", "src/sub/f.PY"]


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """テスト用のディレクトリ木を作る。"""
    for rel in FILES:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("", encoding="utf-8")
    return tmp_path


def rel(root: Path, paths: Iterable[Path]) -> list[str]:
    """root からの相対パスにして並べる。"""
    return sorted(p.relative_to(root).as_posix() for p in paths)


def test_recursive_glob_and_rglob(tree: Path) -> None:
    """** で再帰し、rglob('*.py') は glob('**/*.py') と同じ。隠しファイルも含む。"""
    expected = [".git/e.py", "a.py", "src/.hidden.py", "src/c.py", "src/sub/d.py"]
    assert rel(tree, tree.glob("**/*.py")) == expected
    assert rel(tree, tree.rglob("*.py")) == expected
    assert rel(tree, tree.glob("*.py")) == ["a.py"]


def test_yields_path_objects_relative_to_base(tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Path を yield し、基点が絶対なら絶対パス、相対なら ./ の無い相対パス。"""
    it = tree.glob("*.py")
    assert not isinstance(it, list)
    first = next(it)
    assert isinstance(first, Path) and first.is_absolute()
    monkeypatch.chdir(tree)
    assert sorted(str(p) for p in Path(".").glob("**/*.py")) == [".git/e.py", "a.py", "src/.hidden.py", "src/c.py", "src/sub/d.py"]


def test_hidden_files_differ_from_glob_module(tree: Path) -> None:
    """Path.glob は隠しファイルを含み、glob.glob は既定で除く。"""
    from_pathlib = rel(tree, tree.glob("**/*.py"))
    from_module = sorted(glob.glob("**/*.py", root_dir=tree, recursive=True))
    assert ".git/e.py" in from_pathlib and "src/.hidden.py" in from_pathlib
    assert from_module == ["a.py", "src/c.py", "src/sub/d.py"]


def test_matches_directories_too(tree: Path) -> None:
    """* はディレクトリにもマッチする。末尾 / ならディレクトリだけ。is_file() で絞る。"""
    assert rel(tree, tree.glob("*")) == [".git", "a.py", "b.txt", "src"]
    assert rel(tree, tree.glob("*/")) == [".git", "src"]
    assert rel(tree, (p for p in tree.glob("*") if p.is_file())) == ["a.py", "b.txt"]


def test_double_star_alone_depends_on_version(tree: Path) -> None:
    """** で終わるパターンは 3.12 まではディレクトリだけ、3.13 以降はファイルも返す。"""
    got = rel(tree, tree.glob("**"))
    dirs = [".", ".git", "src", "src/sub"]
    if sys.version_info < (3, 13):
        assert got == dirs
    else:
        assert got == sorted(dirs + FILES)
    assert rel(tree, tree.glob("**/*")) == sorted([".git", "src", "src/sub"] + FILES)


def test_case_sensitivity(tree: Path) -> None:
    """POSIX では既定で大文字小文字を区別する。case_sensitive=False で *.PY にも合う。"""
    if sys.platform == "win32":
        pytest.skip("Windows は既定で区別しない")
    assert "src/sub/f.PY" not in rel(tree, tree.glob("**/*.py"))
    assert "src/sub/f.PY" in rel(tree, tree.glob("**/*.py", case_sensitive=False))


def test_symlinked_directory_is_not_followed(tree: Path) -> None:
    """** の再帰中にシンボリックリンクのディレクトリは辿らない（glob.glob は辿る）。"""
    try:
        os.symlink(tree / "src", tree / "link")
    except (OSError, NotImplementedError) as err:  # Windows や権限の無い環境
        pytest.skip(f"シンボリックリンクを作れない環境: {err}")
    assert not any(p.startswith("link/") for p in rel(tree, tree.glob("**/*.py")))
    assert "link/c.py" in glob.glob("**/*.py", root_dir=tree, recursive=True)


def test_no_match_and_missing_base_are_empty(tree: Path) -> None:
    """マッチ無しも基点ディレクトリ無しも空で、例外にならない。"""
    assert list(tree.glob("*.zzz")) == []
    assert list((tree / "nope").glob("**/*")) == []


def test_invalid_patterns_raise(tree: Path) -> None:
    """空パターンは ValueError、絶対パスのパターンは NotImplementedError。"""
    with pytest.raises(ValueError):
        list(tree.glob(""))
    with pytest.raises(NotImplementedError):
        list(tree.glob("/abs/*.py"))


def test_character_class_but_no_brace_expansion(tree: Path) -> None:
    """[ab] は使えるが {a,b} は展開されない。"""
    assert rel(tree, tree.glob("[ab].*")) == ["a.py", "b.txt"]
    assert list(tree.glob("{a,b}.py")) == []


def test_exclude_by_parts(tree: Path) -> None:
    """Usage: 除外は parts で自分で行う。"""
    got = [p for p in tree.glob("**/*.py") if ".git" not in p.parts]
    assert rel(tree, got) == ["a.py", "src/.hidden.py", "src/c.py", "src/sub/d.py"]
