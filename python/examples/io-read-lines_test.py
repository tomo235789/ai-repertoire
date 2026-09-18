"""io-read-lines: open() + for line in f の Contract を検証する。"""

from pathlib import Path

import pytest


def test_keeps_trailing_newline_and_rstrip(tmp_path: Path) -> None:
    """行末の改行は残り、最終行に改行が無ければその行だけ無い。rstrip('\\n') で落とす。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"a\nb")
    with open(p, encoding="utf-8") as f:
        assert list(f) == ["a\n", "b"]
    assert "a\n".rstrip("\n") == "a"
    assert "a \n".rstrip("\n") == "a "
    assert "a \n".rstrip() == "a"


def test_universal_newlines_by_default(tmp_path: Path) -> None:
    """既定では \\r\\n も単独の \\r も \\n に変換される。newline='' なら変換しない。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"a\r\nb\rc\n")
    with open(p, encoding="utf-8") as f:
        assert list(f) == ["a\n", "b\n", "c\n"]
        assert set(f.newlines) == {"\r", "\n", "\r\n"}
    with open(p, encoding="utf-8", newline="") as f:
        assert list(f) == ["a\r\n", "b\r", "c\n"]


def test_trailing_newline_edge_cases(tmp_path: Path) -> None:
    """末尾の改行 1 つは空行にならない。'a\\n\\n' は 2 行、空ファイルは 0 行、'\\n' だけなら 1 行。"""
    p = tmp_path / "a.txt"
    cases = {b"a\nb\n": ["a\n", "b\n"], b"a\n\n": ["a\n", "\n"], b"": [], b"\n": ["\n"]}
    for data, expected in cases.items():
        p.write_bytes(data)
        with open(p, encoding="utf-8") as f:
            assert list(f) == expected, data


def test_is_lazy(tmp_path: Path) -> None:
    """先頭 1 行を取り出した時点ではファイル全体を読んでいない。"""
    p = tmp_path / "big.txt"
    with open(p, "w", encoding="utf-8") as f:
        for i in range(100_000):
            f.write(f"line {i}\n")
    size = p.stat().st_size
    with open(p, encoding="utf-8") as f:
        assert next(f) == "line 0\n"
        assert 0 < f.buffer.tell() < size


def test_iteration_is_consuming(tmp_path: Path) -> None:
    """break 後は続きから読め、最後まで読んだ後は空。反復中の tell() は OSError。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"1\n2\n3\n")
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line == "2\n":
                break
        with pytest.raises(OSError):
            f.tell()
        assert list(f) == ["3\n"]
        assert list(f) == []


def test_open_errors(tmp_path: Path) -> None:
    """存在しなければ FileNotFoundError、ディレクトリなら IsADirectoryError。"""
    with pytest.raises(FileNotFoundError):
        open(tmp_path / "nope.txt", encoding="utf-8")
    with pytest.raises(IsADirectoryError):
        open(tmp_path, encoding="utf-8")


def test_decode_error_is_raised_per_buffer(tmp_path: Path) -> None:
    """不正なバイト列はそれを含むバッファを読んだ時点で UnicodeDecodeError。小さいファイルでは 1 行も取り出せない。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"ok\n\xff\n")
    got = []
    with pytest.raises(UnicodeDecodeError):
        with open(p, encoding="utf-8") as f:
            for line in f:
                got.append(line)
    assert got == []
    with open(p, encoding="utf-8", errors="replace") as f:
        assert list(f) == ["ok\n", "\ufffd\n"]

    p.write_bytes(b"ok\n" * 100_000 + b"\xff\n")
    count = 0
    with pytest.raises(UnicodeDecodeError):
        with open(p, encoding="utf-8") as f:
            for _ in f:
                count += 1
    assert 0 < count < 100_000


def test_closed_after_with(tmp_path: Path) -> None:
    """with を抜けると閉じられ、以降の反復は ValueError。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"a\n")
    with open(p, encoding="utf-8") as f:
        pass
    assert f.closed
    with pytest.raises(ValueError):
        list(f)


def test_bom_handling(tmp_path: Path) -> None:
    """utf-8 では BOM が最初の行に残り、utf-8-sig では除かれる。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"\xef\xbb\xbfa\n")
    with open(p, encoding="utf-8") as f:
        assert list(f) == ["\ufeffa\n"]
    with open(p, encoding="utf-8-sig") as f:
        assert list(f) == ["a\n"]


def test_read_text_splitlines_alternative(tmp_path: Path) -> None:
    """Alternatives: read_text().splitlines() は改行を含まず、末尾の改行で空要素が増えない。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"a\r\nb\n\nc\n")
    assert p.read_text(encoding="utf-8").splitlines() == ["a", "b", "", "c"]
    assert p.read_text(encoding="utf-8").split("\n") == ["a", "b", "", "c", ""]


def test_binary_mode_splits_on_lf_only(tmp_path: Path) -> None:
    """'rb' では b'\\n' だけが区切りで \\r は残る。"""
    p = tmp_path / "a.txt"
    p.write_bytes(b"a\r\nb\r\n")
    with open(p, "rb") as f:
        assert list(f) == [b"a\r\n", b"b\r\n"]
