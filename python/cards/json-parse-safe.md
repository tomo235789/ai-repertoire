---
id: json-parse-safe
lang: python
title: JSON 文字列を例外を投げずに解析する
tags: [JSON 解析, 例外を値に, 安全なパース, parse, json, loads, safe-parse]
lib: stdlib
fn: json.loads
since: "3.0"
verified: 2026-09-17
status: public
---

`json.loads` を `try/except json.JSONDecodeError` で包み、失敗を例外オブジェクトとして受け取る。結果は `Any` なので、形が必要ならスキーマ検証（pydantic）につなぐ。

## Signature

```python
try: json.loads(text) except json.JSONDecodeError as e: ...
```

## Usage

```python
import json

def parse_safe(text: str) -> tuple[ValueError | None, object]:
    try:
        return None, json.loads(text)
    except ValueError as e:  # JSONDecodeError の親。4300 桁超の整数は素の ValueError
        return e, None

parse_safe('{"name": "alice"}')  # => (None, {'name': 'alice'})
parse_safe("{oops")  # => (JSONDecodeError('Expecting property name enclosed in double quotes: line 1 column 2 (char 1)'), None)
```

## Contract

- 解析できれば Python の値（`dict` / `list` / `str` / `int` / `float` / `bool` / `None`）を返す。トップレベルの `null` / 数値 / 文字列も正当な JSON
- 構文の失敗は `json.JSONDecodeError`（`ValueError` のサブクラス）。`msg`（`Expecting value` など）/ `doc`（元の文字列）/ `pos`（0 始まりの位置）/ `lineno` / `colno` を持ち、`str(e)` は `msg: line 1 column 2 (char 1)`
- 失敗する入力: `''`、`'undefined'`、`'{a:1}'`（引用符なしキー）、`'{"a":1,}'`（末尾カンマ）、`"'x'"`（シングルクォート）、`'nan'` / `'inf'`（小文字）、`'01'`、`'1.'`、`'.5'`、`'{"a":1}{"b":2}'`（Extra data）、`'{"a":1}//c'`、制御文字入りの文字列、UTF-8 BOM 付き
- 成功するが注意が要る入力: `'NaN'` / `'Infinity'` / `'-Infinity'` は `float('nan')` / `inf` になる。`'1e400'` は `inf`。`'{"a":1,"a":2}'` の重複キーは後勝ちで `{'a': 2}`。`'"\\ud800"'`（孤立サロゲート）は通る。前後の空白・改行は無視する
- 整数は桁落ちしない（`'12345678901234567890'` はそのまま `int`）。ただし 4300 桁を超える整数は `JSONDecodeError` ではない素の `ValueError`（`Exceeds the limit ... for integer string conversion`）を投げる
- 文字列以外を渡すと `TypeError`（`bytes` / `bytearray` は可で、エンコーディングを自動判定する）
- `object_hook` / `object_pairs_hook`（`dict` の代わりに `(key, value)` のリストを受ける。重複キーの検出に使える）/ `parse_float` / `parse_int` / `parse_constant`（`NaN` / `Infinity` を受けたとき呼ばれる）で値を差し替えられる。フックの中で投げた例外はそのまま伝わる

## Alternatives

- 例外のままでよければ素の `json.loads`
- 解析と検証を一度にやるなら pydantic の `Model.model_validate_json(text)`（不正な JSON は `json_invalid` の `ValidationError`、カード validation-parse-schema）
- 速度が必要なら orjson（`orjson.loads`。失敗は `orjson.JSONDecodeError`、これも `ValueError` のサブクラス）。ここでは名前のみ

## Pitfalls

- JS の `JSON.parse` と違い `NaN` / `Infinity` を受け付ける。拒否したいなら `parse_constant` で `ValueError` を投げる（`JSONDecodeError` にはならないので `except ValueError` で受ける）
- 4300 桁超の整数は `except json.JSONDecodeError` をすり抜ける。信用できない入力には `except ValueError` で受けるか、`parse_int` で桁数を絞る
- `json.loads(text)` の戻り値は `Any`。`dict` と決めつけて `["name"]` を引くと、`'[1]'` のような入力で `TypeError` になる。pydantic で形を検証する
- 重複キーは黙って後勝ちになる。検出したいなら `object_pairs_hook`
- `except json.JSONDecodeError` は `TypeError`（`None` を渡したとき）を捕まえない。入力が文字列であることは呼ぶ側で保証する

## Test

`examples/json-parse-safe_test.py`
