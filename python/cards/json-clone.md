---
id: json-clone
lang: python
title: ネストした値を深く複製する
tags: [深いコピー, ディープクローン, 複製, clone, deep-copy, deepcopy, immutable]
lib: stdlib
fn: copy.deepcopy
since: "3.0"
verified: 2026-09-17
status: public
---

ネストした `dict` / `list` / `set` / クラスインスタンスを全階層で複製し、元の値と切り離す。状態のスナップショットや、変更前の値を保存したいときに使う。

## Signature

```python
copy.deepcopy(x, memo=None)
```

## Usage

```python
import copy
from datetime import date

src = {"when": date(2020, 1, 1), "tags": {"a"}, "nested": {"n": [1, 2]}}
dup = copy.deepcopy(src)
dup["nested"]["n"].append(3)
dup["tags"].add("b")
src  # => {'when': datetime.date(2020, 1, 1), 'tags': {'a'}, 'nested': {'n': [1, 2]}}（元は変わらない）
dup["nested"] is src["nested"]  # => False
```

## Contract

- 可変なコンテナ（`dict` / `list` / `set` / 可変要素を含む `tuple`）を全階層で新しく作り、元の値は変更しない。戻り値の型は入力と同じ（`OrderedDict` / `defaultdict`（`default_factory` も保持）/ `dict` のサブクラスもそのまま）
- 不変な値（`str` / `int` / `float` / `bytes` / `None` / 不変要素だけの `tuple` / コンパイル済み正規表現 / `Enum` メンバー）は複製せず同じ参照を返す。`frozenset` と `date` / `datetime` は新しいオブジェクトになる（値は等しい）
- 循環参照を保ったまま複製する（`dup["self"] is dup`）。同じオブジェクトへの複数参照も複製後に同一参照のまま（`dup["x"] is dup["y"]`）
- クラスインスタンスは同じクラスの新しいインスタンスになり、`__dict__` / `__slots__` の属性を再帰的に複製する。メソッド・プロパティは保たれる。`dataclass` も同じ
- 関数 / クラス / 組み込み関数 / バウンドメソッドは複製せず同じ参照を返す
- モジュール / ジェネレータ / `threading.Lock` / 開いたファイルなど pickle できないものを含むと `TypeError: cannot pickle 'X' object`。ツリーのどこかに 1 つでもあれば全体が失敗する
- `__deepcopy__(self, memo)` を定義したクラスはそれが呼ばれる。中で `copy.deepcopy(self.attr, memo)` と `memo` を渡すと、循環と共有参照の追跡が引き継がれる。`return self` で複製しない値にもできる
- 第 2 引数 `memo`（`{id(obj): copy}` の `dict`）を渡すと、同じ `memo` で複数回呼んだときに同じ元オブジェクトが同じ複製に対応する。`{id(shared): shared}` を先に入れておくと、その値だけ複製せず共有できる
- ネストが深いと `RecursionError`（既定の再帰上限 1000 で、2000 段の入れ子は失敗する）

## Alternatives

- 1 階層だけなら `copy.copy(d)` / `dict(d)` / `{**d}` / `list(xs)` / `xs[:]`。ネストした値は同じ参照のままなので、`dup["nested"]["n"].append(3)` は元にも反映される
- JSON にできる値だけなら `json.loads(json.dumps(v))` でも複製できるが、`tuple` → `list`、`int` キー → `str` キーになり、`date` / `set` は `TypeError`
- `dataclass` なら `dataclasses.replace(obj, field=value)` で一部を変えた浅いコピーが作れる（ネストしたフィールドは共有）
- pydantic のモデルは `model_copy(deep=True)`

## Pitfalls

- `structuredClone` はクラスインスタンスをプレーンオブジェクトにし関数で `DataCloneError` を投げるが、`deepcopy` はクラスを保ち関数は参照のままコピーする。一方でモジュールやロック、ファイルを持つオブジェクト（DB 接続、ロガー入りの設定など）は `TypeError` になる。`__deepcopy__` でその属性だけ共有にする
- `copy.copy` / `dict(d)` は浅いコピー。ネストした `dict` / `list` を書き換えると元も変わる。`dup["nested"] is src["nested"]` で見分ける
- 大きな構造を毎回複製すると重い。読み取りだけなら複製せず、書き換える部分だけ `{**d, "k": new}` で作り直す
- 例外オブジェクトも複製されるので `dup is err` は `False`。`args` は同じ

## Test

`examples/json-clone_test.py`
