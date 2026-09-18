---
id: json-stringify-stable
lang: python
title: オブジェクトをキー順を揃えた決定的な JSON 文字列にする
tags: [決定的な JSON, キーソート, ハッシュ用文字列, dumps, stable, deterministic, canonical]
lib: stdlib
fn: json.dumps
since: "3.0"
verified: 2026-09-17
status: public
---

`sort_keys=True` で全階層のキーを昇順に並べ、`separators` で空白を落とし、同じ内容なら挿入順によらず同じ文字列にする。キャッシュキー・ハッシュ・スナップショット比較に使う。

## Signature

```python
json.dumps(obj, *, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=None, allow_nan=True)
```

## Usage

```python
import json

def stable(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

stable({"b": 1, "a": {"d": 2, "c": 3}})  # => '{"a":{"c":3,"d":2},"b":1}'
json.dumps({"b": 1, "a": {"d": 2, "c": 3}})  # => '{"b": 1, "a": {"d": 2, "c": 3}}'（挿入順・空白入り）
stable({"b": 1, "a": 2}) == stable({"a": 2, "b": 1})  # => True
```

## Contract

- `sort_keys=True` は全階層の `dict` のキーをソートする（リストの中の `dict` も）。リストの順序は変えない。`OrderedDict` も同じ扱い
- キーの比較は文字列としてではなく元の値で行う。文字列キーは文字列比較（`"10"` < `"2"` < `"B"` < `"_"` < `"a"` < `"あ"`、コードポイント順）で、`int` キーは数値順（`{2: ..., 10: ...}` → `{"2":...,"10":...}`）
- 文字列以外のキーは出力時に文字列化する。`True` → `"true"`、`None` → `"null"`、`3` → `"3"`、`1.5` → `"1.5"`。`tuple` などはキーにできず `TypeError`（`skipkeys=True` で黙って落とせる）
- `sort_keys=True` で型の混ざったキー（`str` と `int`、`None` と `int`）があると比較できず `TypeError`。同じ `dict` に `1` と `"1"` があると `sort_keys` 無しでは `{"1": "a", "1": "b"}` と重複して出る
- `separators=(",", ":")` で区切りの空白を無くす。既定は `(", ", ": ")`。`indent` を付けると改行と字下げが入り、別の文字列になる
- `ensure_ascii=False` で非 ASCII をそのまま出す。既定の `True` では `"名"` のようにエスケープされる（どちらも決定的だが文字列は違う）
- 値の対応: `None` → `null`、`True` → `true`、`tuple` → 配列、`int` は桁落ちなし（`10**20` → `100000000000000000000`）、`float` は `repr`（`1.0` → `1.0`、`1e16` → `1e+16`）、`IntEnum` は数値
- `date` / `datetime` / `Decimal` / `set` / `bytes` / `dataclass` / `Enum`（`IntEnum` 以外）は `TypeError: Object of type X is not JSON serializable`。`default=` に変換関数を渡すと、直列化できない値ごとに呼ばれる。`default` の戻り値もさらに `sort_keys` の対象
- 循環参照は `ValueError: Circular reference detected`。同じオブジェクトへの複数参照（循環ではない）はそれぞれの場所に展開する
- `nan` / `inf` は既定で `NaN` / `Infinity`（JSON 規格外）として出る。`allow_nan=False` で `ValueError`

## Alternatives

- 順序が問題にならない（自分で作った `dict` をその場で使う）なら `json.dumps(obj)` で十分
- ハッシュにするなら `hashlib.sha256(stable(obj).encode()).hexdigest()`
- 比較だけが目的なら文字列にせず `==`（カード json-deep-equal）
- 速度や `dataclass` / `datetime` の自動変換が欲しいなら orjson（`orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)`、戻り値は `bytes`）。ここでは名前のみ

## Pitfalls

- `sort_keys=True` を付けないと挿入順のまま。Python 3.7 以降の `dict` は挿入順を保つので、同じ内容でも作り方が違えば文字列が変わる
- safe-stable-stringify は循環参照を `"[Circular]"` に置き換え `bigint` を数値で出すが、`json.dumps` は循環で `ValueError`、`int` は桁数によらず数値で出る。JS 側で読み戻すと `9007199254740993` は精度が落ちる
- JS の `JSON.stringify` は整数風キーを数値順で先頭に置くが、Python の文字列キーは純粋な文字列比較（`"10"` が `"2"` の前）。言語をまたいで同じハッシュを得たいなら、キーを文字列に揃えたうえで同じ順序規則を確認する
- `default=str` は手軽だが `Decimal("1.10")` → `"1.10"`、`date` → `"2020-01-01"` のように型情報が消え、読み戻しても元に戻らない
- `float` は `0.1 + 0.2` が `0.30000000000000004` のように `repr` で出る。丸めたいなら値を先に `round` する

## Test

`examples/json-stringify-stable_test.py`
