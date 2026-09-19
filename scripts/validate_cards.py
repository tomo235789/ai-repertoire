#!/usr/bin/env python3
"""カードの検証。PR の CI で走らせる。

- frontmatter が schema/card.schema.json に合う
- lang がディレクトリ名と一致、ファイル名が id と一致
- 固定見出しが順序どおり揃い、余計な ## が無い
- ## Usage のコードが 10 行以内
- ## Test のパスが存在する
- Python のカードは ## Signature と ## Usage が実装のシグネチャと食い違わない
- 同じ id の title が言語間で一致
- --public-only 時は status が public 以外なら失敗（公開リポジトリ用）
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, List, Tuple

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

# examples が Python のディレクトリ。ここだけ Signature と Usage を実装と突き合わせる
PYTHON_LANGS = frozenset({"python", "sql", "aws", "gcp", "azure"})


FunctionNode = "ast.FunctionDef | ast.AsyncFunctionDef"


def _public_functions(source: str) -> Dict[str, "FunctionNode"]:
    """モジュール直下の公開関数を名前で引けるようにする。async def も含む"""
    return {
        node.name: node
        for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }


def _parameter_names(node: "FunctionNode") -> List[str]:
    """引数名を宣言順に返す。*args と **kwargs も名前として数える"""
    args = node.args
    names = [a.arg for a in args.posonlyargs + args.args]
    if args.vararg is not None:
        names.append(args.vararg.arg)
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg is not None:
        names.append(args.kwarg.arg)
    return names


def _required_parameters(node: "FunctionNode") -> Tuple[List[str], List[str]]:
    """既定値を持たない引数を (位置指定, キーワード専用) で返す。可変長引数は数えない"""
    args = node.args
    positional = args.posonlyargs + args.args
    without_default = positional[: len(positional) - len(args.defaults)]
    # kwonlyargs と kw_defaults は同じ長さ。既定値が None の要素が必須
    keyword_only = [a for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is None]
    return [a.arg for a in without_default], [a.arg for a in keyword_only]


def _documented_parameters(text: str) -> List[str]:
    """Signature の引数リストから名前だけを取り出す。

    `*` と `/` は区切りなので落とす。`*args` と `**kwargs` は名前として扱う。
    入れ子の括弧（型注釈や既定値）の中のカンマでは区切らない。
    """
    names: List[str] = []
    depth = 0
    current = ""
    for char in text + ",":
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        if char == "," and depth == 0:
            token = current.strip()
            current = ""
            if not token or token in ("*", "/"):
                continue
            name = token.split(":", 1)[0].split("=", 1)[0].strip().lstrip("*")
            if name:
                names.append(name)
            continue
        current += char
    return names


def _section(card: Card, heading: str) -> str:
    """指定した見出しの本文を返す。無ければ空文字"""
    for name, body in card.sections:
        if name == heading:
            return body
    return ""


def validate_signature(card: Card, source: str) -> List[str]:
    """## Signature に書いた引数が実装と合っているか"""
    functions = _public_functions(source)
    section = _section(card, "Signature")
    errors = []
    for name, node in functions.items():
        # `def` の有無はカードによって揺れるので、どちらでも拾う。async も同じ
        match = re.search(
            rf"^(?:async\s+)?(?:def\s+)?{re.escape(name)}\((.*?)\)\s*->", section, re.M | re.S
        )
        if match is None:
            errors.append(f"Signature: {name} の定義が無い")
            continue
        documented = _documented_parameters(match.group(1))
        actual = _parameter_names(node)
        missing = [p for p in actual if p not in documented]
        if missing:
            errors.append(f"Signature: {name} に {missing} が書かれていない")
        extra = [p for p in documented if p not in actual]
        if extra:
            errors.append(f"Signature: {name} に実装に無い引数 {extra} が書かれている")
    return errors


def validate_usage_call(card: Card, source: str) -> List[str]:
    """## Usage の呼び出しで必須引数が埋まっているか"""
    functions = _public_functions(source)
    section = _section(card, "Usage")
    code = re.search(r"```python\n(.*?)```", section, re.S)
    if code is None:
        return []
    try:
        tree = ast.parse(code.group(1))
    except SyntaxError:
        # Usage は断片なので構文が通らないことがある。そのときは検査しない
        return []
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        target = functions.get(node.func.id)
        if target is None:
            continue
        given = {kw.arg for kw in node.keywords if kw.arg}
        positional_count = len(node.args)
        arguments = target.args
        position_only = {a.arg for a in arguments.posonlyargs}
        # **kwargs が無ければ、位置専用の引数名をキーワードで渡すことはできない
        if arguments.kwarg is None:
            by_keyword = sorted(given & position_only)
            if by_keyword:
                errors.append(
                    f"Usage: {node.func.id} の位置専用の引数 {by_keyword} を"
                    "キーワードで渡している"
                )
        required_positional, required_keyword = _required_parameters(target)
        # 位置引数は前から順に埋まる。位置専用の引数は名前では埋められない
        missing = [
            name for index, name in enumerate(required_positional)
            if index >= positional_count
            and (name in position_only or name not in given)
        ]
        # キーワード専用は名前でしか埋まらない
        missing += [name for name in required_keyword if name not in given]
        # *args が無ければ、受け取れる位置引数の数には上限がある
        if arguments.vararg is None:
            limit = len(arguments.posonlyargs) + len(arguments.args)
            if positional_count > limit:
                errors.append(
                    f"Usage: {node.func.id} に位置引数を渡しすぎている"
                    f"（{positional_count} 個。受け取れるのは {limit} 個）"
                )
        if missing:
            errors.append(f"Usage: {node.func.id} の呼び出しに {missing} が無い")
    return errors


def validate_against_implementation(card: Card, read: Callable[[str], str]) -> List[str]:
    """Python のカードだけ、Signature と Usage を実装と突き合わせる"""
    if card.lang not in PYTHON_LANGS:
        return []
    path = f"{card.lang}/examples/{card.id}.py"
    source = read(path)
    if source is None:
        return []
    try:
        return validate_signature(card, source) + validate_usage_call(card, source)
    except SyntaxError as exc:
        return [f"{path}: 構文が壊れている（{exc}）"]


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
    card: Card,
    validator: Draft202012Validator,
    exists: Callable[[str], bool],
    public_only: bool,
    read: Callable[[str], str] = lambda _: None,
) -> List[str]:
    return (
        validate_meta(card, validator)
        + validate_location(card)
        + validate_headings(card)
        + validate_usage(card)
        + validate_test_path(card, exists)
        + validate_status(card, public_only)
        + validate_against_implementation(card, read)
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

    def read_source(rel_path: str) -> str:
        path = root / rel_path
        return path.read_text(encoding="utf-8") if path.is_file() else None

    for card in cards:
        for msg in validate_card(
            card, validator, lambda p: (root / p).is_file(), args.public_only, read_source
        ):
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
