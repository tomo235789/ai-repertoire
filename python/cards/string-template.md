---
id: string-template
lang: python
title: テンプレート文字列に値を埋め込む
tags: [テンプレート, 文字列の埋め込み, 差し込み, プレースホルダー, template, substitute, placeholder, string.Template]
lib: stdlib
fn: string.Template
since: "3.0"
verified: 2026-09-17
status: public
---

`$name` / `${name}` のプレースホルダーを持つテンプレートに、マッピングやキーワード引数の値を埋め込む。式の評価や属性アクセスを **しない** ので、設定ファイルやユーザー由来のテンプレートに値を入れるのに使う。

## Signature

```python
string.Template(template).substitute(mapping={}, /, **kwds)  # safe_substitute も同じ引数
```

## Usage

```python
from string import Template

t = Template("Hello, $name! You have ${count} items. Cost: $$5")
t.substitute(name="Ann", count=3)       # => 'Hello, Ann! You have 3 items. Cost: $5'
t.substitute({"name": "Ann"}, count=3)  # マッピングとキーワードの併用（同じキーはキーワードが優先）
t.safe_substitute(name="Ann")           # => 'Hello, Ann! You have ${count} items. Cost: $5'（無いものは残す）
t.substitute(name="Ann")                # => raises KeyError: 'count'
```

## Contract

- プレースホルダーは `$identifier` と `${identifier}`。識別子は `[_a-zA-Z][_a-zA-Z0-9]*` で、`$name_x` は `name_x` 1 語として扱われる。語の直後に文字を続けるなら `${name}_x`。`$$` は `$` 1 文字になる
- `substitute` は足りないキーで `KeyError(キー名)`、`$1` や末尾の `$` のような不正なプレースホルダーで `ValueError('Invalid placeholder in string: line 1, col 1')` を投げる
- `safe_substitute` は足りないキーのプレースホルダーを **そのまま残し**、不正なプレースホルダーも例外にせず残す。常に文字列を返す
- 値は `str()` で文字列化される（`None` → `'None'`、`3` → `'3'`、リストはその `repr`）。書式指定（桁数・小数点）は無い
- 第 1 引数は任意のマッピング（`os.environ` / `ChainMap` など `__getitem__` を持つもの）。マッピングとキーワード引数を併用すると **キーワードが優先**
- `$s.password` は `$s` だけを置換し `.password` は文字のまま残る。`str.format` の `{s.password}` のような属性アクセスは起きない。`t.template` で元の文字列、`t.get_identifiers()`（3.11）で使われている識別子の一覧、`t.is_valid()`（3.11）で不正なプレースホルダーの有無を確認できる

## Alternatives

- テンプレートがコード中の定数なら f-string（`f"Hello, {name}!"`）。書式指定が使え、最も速い
- 書式指定つきで実行時にテンプレートを選ぶなら `"Hello, {name}!".format(**values)`。ただし **テンプレートがユーザー由来なら使わない**（`{obj.__class__}` のような属性アクセスで内部情報が漏れる）
- 条件分岐やループが要るなら `jinja2`（サンドボックスは `SandboxedEnvironment`）
- 区切り文字を変えるなら `class MyTemplate(Template): delimiter = "%"`

## Pitfalls

- TypeScript（es-toolkit の `template`）は任意の JS を実行するが、`string.Template` は単純な置換だけ。逆に `<%= %>` の式評価や HTML エスケープは無いので、HTML に埋め込むなら `html.escape` を値に掛けてから渡す
- `str.format` と違い `{` `}` は文字のまま（JSON の断片をテンプレートにできる）。代わりに `$` が特別なので、金額などの `$` は `$$` にする
- `safe_substitute` は例外を出さないので、キーの綴り間違いに気付けない。開発中は `substitute` で検出し、外部入力のテンプレートにだけ `safe_substitute` を使う
- 値の書式（`f"{price:.2f}"` 相当）は Template 側でできない。埋め込む前に文字列にする
- `$name` の直後に英数字や `_` を続けられない（`$names` は `names` になる）。`${name}s` と書く

## Test

`examples/string-template_test.py`
