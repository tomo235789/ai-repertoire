"""io-join-path: pathlib.Path の / 演算子の Contract を検証する。"""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest


def test_joins_segments_and_returns_new_path() -> None:
    """断片をつなぎ、新しい Path を返す。元は変わらない。"""
    base = Path("logs")
    joined = base / "app" / "x.log"
    assert joined == Path("logs/app/x.log")
    assert base == Path("logs")
    assert Path("a").joinpath("b", "c") == Path("a", "b", "c") == Path("a/b/c")


def test_normalizes_dot_and_duplicate_separators_but_keeps_dotdot() -> None:
    """. と重複した区切りは消え、空文字列は無視されるが、.. は残る。"""
    assert Path("a") / "./b" / "" == Path("a/b")
    assert Path("a//b") == Path("a/b")
    joined = Path("logs/app") / "../db" / "x.sqlite"
    assert joined.parts == ("logs", "app", "..", "db", "x.sqlite")
    assert str(joined) == "logs/app/../db/x.sqlite"
    assert os.path.normpath(joined) == "logs/db/x.sqlite"


def test_absolute_right_operand_wins() -> None:
    """右辺が絶対パスなら、それまでの部分は捨てられる。os.path.join も同じ。"""
    assert Path("/var") / "/log" == Path("/log")
    assert Path("/a/b") / "/c" / "d" == Path("/c/d")
    assert os.path.join("/var", "/log") == "/log"


def test_trailing_separator_is_dropped() -> None:
    """末尾の / は保持しない。Path('') は '.'。"""
    assert str(Path("a/") / "b/") == "a/b"
    assert str(Path("")) == "."
    assert os.path.join("a", "") == "a/"


def test_operand_types() -> None:
    """str・Path・PathLike は可。int や None は TypeError。左辺が str でもよい。"""
    assert Path("a") / Path("b") == Path("a/b")
    assert "a" / Path("b") == Path("a/b")
    with pytest.raises(TypeError):
        Path("a") / 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        Path("a") / None  # type: ignore[operator]


def test_pure_paths_are_os_independent() -> None:
    """PurePosixPath は / のみ、PureWindowsPath は \\ を区切りにし、ドライブごと置き換わる。"""
    assert (PurePosixPath("a") / "b\\c").parts == ("a", "b\\c")
    assert str(PureWindowsPath("C:/a") / "b") == "C:\\a\\b"
    assert str(PureWindowsPath("C:/a") / "/b") == "C:\\b"
    assert str(PureWindowsPath("C:/a") / "D:/b") == "D:\\b"
    assert str(PureWindowsPath("a") / "b\\c") == "a\\b\\c"


def test_resolve_makes_absolute_and_collapses_dotdot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """resolve() はカレントディレクトリからの絶対パスにして .. を解決する。"""
    (tmp_path / "logs" / "app").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    resolved = (Path("logs/app") / "../db").resolve()
    assert resolved.is_absolute()
    assert resolved == tmp_path.resolve() / "logs" / "db"


def test_str_and_fspath() -> None:
    """str() と os.fspath() は同じ文字列。"""
    p = Path("a") / "b"
    assert str(p) == os.fspath(p) == "a/b"


def test_os_path_join_does_not_normalize() -> None:
    """Alternatives: os.path.join は . や重複した / を正規化しない。"""
    assert os.path.join("a//", "./b") == "a//./b"
    assert os.path.join("a", "b") == "a/b"


def test_path_traversal_check(tmp_path: Path) -> None:
    """Pitfalls: ユーザー入力の .. や絶対パスは base の外を指す。resolve() + is_relative_to で検出する。"""
    base = tmp_path / "base"
    base.mkdir()
    assert not (base / "../etc/passwd").resolve().is_relative_to(base.resolve())
    assert not (base / "/etc/passwd").resolve().is_relative_to(base.resolve())
    assert (base / "sub/x.txt").resolve().is_relative_to(base.resolve())


def test_url_is_not_a_path() -> None:
    """URL を / で組み立てると // が 1 つに潰れる。"""
    assert str(Path("https://x.com") / "a") == "https:/x.com/a"
