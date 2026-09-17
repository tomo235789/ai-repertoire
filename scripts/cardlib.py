"""カード（*/cards/*.md）の読み取りに関する純粋関数群。

validate_cards.py と build_reference.py の両方から使う。
ファイル I/O は load_cards() だけに閉じ込める。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

# 固定見出し（順序固定）。これ以外の ## は禁止
FIXED_HEADINGS: Tuple[str, ...] = ("Signature", "Usage", "Contract", "Alternatives", "Pitfalls", "Test")
REQUIRED_HEADINGS: Tuple[str, ...] = ("Signature", "Usage", "Contract", "Test")

# 対応表・index の列順
LANG_ORDER: Tuple[str, ...] = ("typescript", "python", "go", "csharp", "cpp", "react", "ruby", "rust", "sql")
LANG_LABEL: Dict[str, str] = {
    "typescript": "TypeScript",
    "python": "Python",
    "go": "Go",
    "csharp": "C#",
    "cpp": "C++",
    "react": "React",
    "ruby": "Ruby",
    "rust": "Rust",
    "sql": "SQL",
}

_HEADING_RE = re.compile(r"^## (.+?)\s*$")
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


class CardError(ValueError):
    """カードの構文が壊れていて読めない"""


@dataclass(frozen=True)
class Card:
    meta: dict
    preamble: str
    sections: Tuple[Tuple[str, str], ...]  # (見出し, 本文) を出現順で
    path: str = ""  # リポジトリルートからの相対パス（表示用）

    @property
    def id(self) -> str:
        return str(self.meta.get("id", ""))

    @property
    def lang(self) -> str:
        return str(self.meta.get("lang", ""))

    @property
    def title(self) -> str:
        return str(self.meta.get("title", ""))

    @property
    def headings(self) -> Tuple[str, ...]:
        return tuple(h for h, _ in self.sections)

    def section(self, name: str) -> Optional[str]:
        for heading, body in self.sections:
            if heading == name:
                return body
        return None


def split_frontmatter(text: str) -> Tuple[dict, str]:
    """先頭の YAML frontmatter と本文に分ける"""
    if not text.startswith("---\n"):
        raise CardError("frontmatter がない（先頭が '---' ではない）")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise CardError("frontmatter が閉じていない")
    raw = text[4:end]
    body = text[end + len("\n---\n"):]
    try:
        meta = yaml.safe_load(raw)
    except (yaml.YAMLError, ValueError) as e:  # ValueError: 存在しない日付（2026-99-99 など）
        raise CardError(f"frontmatter の YAML が不正: {e}") from e
    if not isinstance(meta, dict):
        raise CardError("frontmatter がマッピングではない")
    return _normalize_dates(meta), body


def _normalize_dates(meta: dict) -> dict:
    """PyYAML が date 型に変換した値を ISO 文字列へ戻す（schema は文字列で検証する）"""
    out = {}
    for k, v in meta.items():
        if hasattr(v, "isoformat") and not isinstance(v, str):
            out[k] = v.isoformat()
        elif isinstance(v, list):
            out[k] = [_normalize_dates(x) if isinstance(x, dict) else x for x in v]
        elif isinstance(v, dict):
            out[k] = _normalize_dates(v)
        else:
            out[k] = v
    return out


def _fence_toggle(line: str, open_fence: Optional[str]) -> Optional[str]:
    """フェンス状態を更新する。open_fence は開いているフェンス文字列（無ければ None）。
    閉じるのは同じ文字種で開始時以上の長さのときだけ（```` の中の ``` は本文扱い）"""
    m = _FENCE_RE.match(line)
    if not m:
        return open_fence
    fence = m.group(1)
    if open_fence is None:
        return fence
    # 閉じフェンスは同じ文字種・開始時以上の長さで、後ろが空白だけの行（```python は閉じない）
    if fence[0] == open_fence[0] and len(fence) >= len(open_fence) and not line[m.end():].strip():
        return None
    return open_fence


def split_sections(body: str) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    """本文を最初の ## より前（前書き）と、## 単位の節に分ける。コードフェンス内の ## は無視する"""
    preamble_lines: List[str] = []
    sections: List[Tuple[str, List[str]]] = []
    open_fence: Optional[str] = None
    for line in body.splitlines():
        open_fence = _fence_toggle(line, open_fence)
        m = None if open_fence else _HEADING_RE.match(line)
        if m:
            sections.append((m.group(1), []))
        elif sections:
            sections[-1][1].append(line)
        else:
            preamble_lines.append(line)
    return (
        "\n".join(preamble_lines).strip(),
        tuple((h, "\n".join(lines).strip()) for h, lines in sections),
    )


def parse_card(text: str, path: str = "") -> Card:
    meta, body = split_frontmatter(text)
    preamble, sections = split_sections(body)
    return Card(meta=meta, preamble=preamble, sections=sections, path=path)


def test_path(card: Card) -> Optional[str]:
    """## Test の最初の非空行をパスとして返す（バッククォートは剥がす）。言語ディレクトリからの相対"""
    body = card.section("Test")
    if body is None:
        return None
    for line in body.splitlines():
        s = line.strip().strip("`").strip()
        if s:
            return s
    return None


def code_lines(section_body: str) -> int:
    """節の中のコードフェンス内の行数を数える"""
    count = 0
    open_fence: Optional[str] = None
    for line in section_body.splitlines():
        new_fence = _fence_toggle(line, open_fence)
        if new_fence != open_fence:  # フェンスの開閉行そのもの
            open_fence = new_fence
            continue
        if open_fence:
            count += 1
    return count


def lang_sort_key(lang: str) -> Tuple[int, str]:
    return (LANG_ORDER.index(lang) if lang in LANG_ORDER else len(LANG_ORDER), lang)


def load_cards(root: Path) -> List[Card]:
    """<root>/*/cards/*.md をすべて読む。唯一の I/O 関数"""
    cards: List[Card] = []
    for path in sorted(root.glob("*/cards/*.md")):
        rel = path.relative_to(root).as_posix()
        cards.append(parse_card(path.read_text(encoding="utf-8"), path=rel))
    return cards
