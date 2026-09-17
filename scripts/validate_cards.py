#!/usr/bin/env python3
"""カードの検証。PR の CI で走らせる。

- frontmatter が schema/card.schema.json に合う
- lang がディレクトリ名と一致、ファイル名が id と一致
- 固定見出しが順序どおり揃い、余計な ## が無い
- ## Usage のコードが 10 行以内
- ## Test のパスが存在する
- 同じ id の title が言語間で一致
- --public-only 時は status が public 以外なら失敗（公開リポジトリ用）
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, List

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cardlib import (  # noqa: E402
    FIXED_HEADINGS,
    REQUIRED_HEADINGS,
    Card,
    CardError,
    code_lines,
    load_cards,
    parse_card,
    test_path,
)

USAGE_MAX_LINES = 10


def validate_meta(card: Card, validator: Draft202012Validator) -> List[str]:
    return [f"frontmatter: {e.json_path} {e.message}" for e in sorted(validator.iter_errors(card.meta), key=str)]


def validate_location(card: Card) -> List[str]:
    """パス <lang>/cards/<id>.md と frontmatter の整合"""
    parts = card.path.split("/")
    errors = []
    if len(parts) != 3 or parts[1] != "cards":
        return [f"path: <lang>/cards/<id>.md の形ではない: {card.path}"]
    if parts[0] != card.lang:
        errors.append(f"lang: frontmatter は '{card.lang}' だがディレクトリは '{parts[0]}'")
    stem = parts[2][:-3] if parts[2].endswith(".md") else parts[2]
    if stem != card.id:
        errors.append(f"id: frontmatter は '{card.id}' だがファイル名は '{stem}'")
    return errors


def validate_headings(card: Card) -> List[str]:
    errors = []
    headings = card.headings
    extra = [h for h in headings if h not in FIXED_HEADINGS]
    if extra:
        errors.append(f"headings: 固定見出し以外の ## がある: {extra}")
    missing = [h for h in REQUIRED_HEADINGS if h not in headings]
    if missing:
        errors.append(f"headings: 必須見出しが無い: {missing}")
    known = [h for h in headings if h in FIXED_HEADINGS]
    expected = [h for h in FIXED_HEADINGS if h in known]
    if known != expected:
        errors.append(f"headings: 順序が違う。期待 {expected} / 実際 {known}")
    if len(set(headings)) != len(headings):
        errors.append("headings: 同じ見出しが重複している")
    for heading, body in card.sections:
        if heading in REQUIRED_HEADINGS and not body:
            errors.append(f"{heading}: 本文が空")
    return errors


def validate_usage(card: Card) -> List[str]:
    body = card.section("Usage")
    if body is None:
        return []
    n = code_lines(body)
    if n == 0:
        return ["Usage: コードブロックが無い"]
    if n > USAGE_MAX_LINES:
        return [f"Usage: コードが {n} 行。{USAGE_MAX_LINES} 行以内にする"]
    return []


def validate_test_path(card: Card, exists: Callable[[str], bool]) -> List[str]:
    """exists には '<lang>/<相対パス>' を受けて存在を返す関数を注入する"""
    rel = test_path(card)
    if rel is None:
        return ["Test: パスが書かれていない"]
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return [f"Test: <lang> ディレクトリ外のパスは指定できない: {rel}"]
    full = f"{card.lang}/{rel}"
    if not exists(full):
        return [f"Test: ファイルが無い: {full}"]
    return []


def validate_status(card: Card, public_only: bool) -> List[str]:
    if public_only and card.meta.get("status") != "public":
        return [f"status: 公開リポジトリでは public のみ許可（実際: {card.meta.get('status')}）"]
    return []


def validate_card(
    card: Card, validator: Draft202012Validator, exists: Callable[[str], bool], public_only: bool
) -> List[str]:
    return (
        validate_meta(card, validator)
        + validate_location(card)
        + validate_headings(card)
        + validate_usage(card)
        + validate_test_path(card, exists)
        + validate_status(card, public_only)
    )


def validate_titles(cards: List[Card]) -> List[str]:
    """同じ id の title が言語間で一致するか（表記ゆれ検出）"""
    by_id: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    for c in cards:
        by_id[c.id][c.title].append(c.path)
    errors = []
    for cid, titles in sorted(by_id.items()):
        if len(titles) > 1:
            detail = "; ".join(f"'{t}' ({', '.join(paths)})" for t, paths in titles.items())
            errors.append(f"{cid}: title が言語間で一致しない: {detail}")
    return errors


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="リポジトリルート")
    parser.add_argument("--public-only", action="store_true", help="status: public 以外を失敗にする（公開リポジトリ用）")
    args = parser.parse_args(argv)
    root: Path = args.root

    schema = json.loads((root / "schema" / "card.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    errors: List[str] = []
    cards: List[Card] = []
    card_paths = sorted(root.glob("*/cards/*.md"))
    if not card_paths:
        errors.append("cards: カードが 1 枚も見つからない（*/cards/*.md）")
    for path in card_paths:
        rel = path.relative_to(root).as_posix()
        try:
            cards.append(parse_card(path.read_text(encoding="utf-8"), path=rel))
        except CardError as e:
            errors.append(f"{rel}: {e}")

    for card in cards:
        for msg in validate_card(card, validator, lambda p: (root / p).is_file(), args.public_only):
            errors.append(f"{card.path}: {msg}")
    errors.extend(validate_titles(cards))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"\nNG: {len(errors)} 件のエラー / {len(cards)} 枚", file=sys.stderr)
        return 1
    print(f"OK: {len(cards)} 枚のカードを検証")
    return 0


if __name__ == "__main__":
    sys.exit(main())
