---
id: json-deep-equal
lang: python
title: 2 つの値が構造的に等しいか比較する
tags: [深い比較, 構造比較, 等価判定, deep-equal, equality, compare, structural]
lib: stdlib
fn: ==
since: "3.0"
verified: 2026-09-17
status: public
---

`dict` / `list` / `tuple` / `set` の `==` は中身を再帰的に比較するので、ネストした値の構造比較に追加の関数は要らない。設定の変更検知やテストの期待値比較に使う。

## Signature

```python
a == b
```

## Usage

```python
import math

{"a": 1, "b": [1, {"c": 2}]} == {"b": [1, {"c": 2}], "a": 1}  # => True（dict のキー順は無関係）
[1, 2] == [2, 1]              # => False（list は順序あり）
{1, 2} == [1, 2]              # => False（型が違う）
{"a": 1} == {"a": True}       # => True（1 == True）
[float("nan")] == [float("nan")]  # => False（別オブジェクトの NaN。同じオブジェクトなら is で短絡し True）
```

## Contract

- `dict` はキーの集合と各キーの値を比較し、挿入順は見ない（`OrderedDict` 同士だけ順序も見る。`OrderedDict` と `dict` の比較は順序を見ない）。`list` / `tuple` は長さと各要素を順に、`set` / `frozenset` は要素の集合を比較する。すべて再帰的
- コンテナの型が違えば `False`。`[1] == (1,)`、`{1} == [1]`、`[] == {}` はすべて `False`。ただし `set` と `frozenset`、`dict` と `OrderedDict` は等しくなりうる
- 数値は型をまたいで値で比較する。`1 == 1.0 == True`、`0 == False`、`Decimal("1.0") == 1`、`Fraction(1, 2) == 0.5`。`{"a": 1} == {"a": True}` や `{1: "x"} == {True: "x"}` も `True`。`Decimal("0.1") == 0.1` は `False`（2 進浮動小数の値で比較）
- `NaN` は自分自身と等しくない（`math.nan == math.nan` は `False`）が、コンテナの要素比較は先に `is` を見るので同じオブジェクトなら `True`（`n = math.nan; [n] == [n]` は `True`、`[n] == [float("nan")]` は `False`）。`in` / `count` / `index` も同じ
- 型の違うスカラーは `False`。`"1" == 1`、`"a" == b"a"`、`None == 0`、`None == False`。`{"a": None} == {}` も `False`（キーの有無を区別）
- `dataclass` は既定で `__eq__` を持ち、同じクラスで全フィールドが等しければ `True`。クラスが違えば（フィールドが同じでも）`False`。`eq=False` なら同一性比較。素のクラスは `__eq__` を定義しない限り同一性比較（`C(1) == C(1)` は `False`）。`namedtuple` は `tuple` として比較する（`NT(1, 2) == (1, 2)` は `True`）
- `datetime` は naive と aware を比べると `False`。`date` と `datetime` も `False`
- 関数は同じ参照のときだけ `True`
- 循環参照を含む構造同士（別オブジェクト）は `RecursionError`。同じオブジェクト同士なら `is` の短絡で `True`

## Alternatives

- 浮動小数を許容誤差付きで比べるなら `math.isclose` / `pytest.approx`（`0.1 + 0.2 == 0.3` は `False`）
- 順序を無視して `list` を比べるなら `sorted(a) == sorted(b)` か `collections.Counter(a) == Counter(b)`
- 差分が欲しいなら `deepdiff.DeepDiff`（外部ライブラリ）。ここでは名前のみ

## Pitfalls

- es-toolkit の `isEqual` は `NaN` 同士を `true`、`1` と `true` を `false` とするが、Python は逆（`NaN` は `False`、`1 == True` は `True`）。JSON の `{"ok": true}` と `{"ok": 1}` を区別したいなら型も見る（`type(a) is type(b)`）
- `1 == 1.0 == True` なので `{1, 1.0, True}` は `{1}`、`{1: "a", 1.0: "b", True: "c"}` は `{1: "c"}` になる。数値と真偽値をキーに混ぜない
- `json.loads(json.dumps(x)) == x` は `tuple`（`list` になる）や `int` キー（文字列になる）で `False` になる
- `!=` は `==` の否定で、`NaN` を含むコンテナでも `[n] != [n]` は `False`（`is` で短絡）

## Test

`examples/json-deep-equal_test.py`
