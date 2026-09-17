---
id: result-try-to-result
lang: python
title: 例外を投げる関数の結果をタプルで受け取る
tags: [例外を値に, エラーハンドリング, タプル, 結果型, attempt, try-catch, result-tuple]
lib: returns
fn: returns.result.safe
since: "0.20"
verified: 2026-09-17
status: public
---

例外を投げるかもしれない関数を `Success(値)` か `Failure(例外)` を返す関数に変えるデコレータ。`try/except` のネストを避けて分岐を平らにするのに使う。

## Signature

```python
@returns.result.safe
```

## Usage

```python
import json
from returns.result import safe

@safe
def parse(text: str) -> dict:
    return json.loads(text)

parse('{"ok": true}')  # => <Success: {'ok': True}>
parse("{oops")         # => <Failure: Expecting property name ...>（JSONDecodeError を包む）
parse("{oops").value_or({})  # => {}
```

## Contract

- 装飾された関数を呼ぶと即座に元の関数を 1 回実行し、正常に返れば `Success(戻り値)`、例外なら `Failure(例外オブジェクト)` を返す。`None` を返した場合も `Success(None)`
- 捕捉するのは `Exception` のサブクラスだけ。`KeyboardInterrupt` / `SystemExit` などの `BaseException` は捕捉せずそのまま伝わる
- `safe(exceptions=(ValueError,))` の形で捕捉する例外を絞れる。それ以外の例外はそのまま伝わる
- `Success` / `Failure` は `isinstance` と `match` の `case Success(v)` / `case Failure(e)` で判別できる。`Failure` も真偽値は `True` なので `if result:` では判定できない
- `.unwrap()` は `Success` なら中身を返し、`Failure` なら `UnwrapFailedError` を投げる（`__cause__` に元の例外）。`.value_or(default)` は `Failure` なら `default`。`.failure()` は `Failure` の中身を返し、`Success` では `UnwrapFailedError`
- `.map(f)` は `Success` の中身だけを変換し、`Failure` はそのまま通す

## Alternatives

- `async def` には `safe` を付けない（コルーチンオブジェクトが `Success` に包まれ、例外は捕捉されない）。非同期は `returns.future.future_safe`
- 依存を増やせない場合は `try: return (None, fn()) except Exception as e: return (e, None)` のタプルを返す関数を書く
- 失敗時に別の値で復帰するなら `.lash(lambda err: Success(default))`、`Failure` の中身を変換するなら `.alt(f)`

## Pitfalls

- es-toolkit の `attempt` は `[error, value]` のタプルだが、`safe` は `Success` / `Failure` オブジェクト。`err, value = ...` のような分解代入はできない
- `Failure(ValueError("x")) == Failure(ValueError("x"))` は `False`（例外オブジェクトは同一性で比較される）。テストでは `isinstance(result.failure(), ValueError)` で判定する
- `exceptions=` を絞らないと `Exception` 全部が `Failure` になり、バグ（`TypeError` や `AttributeError`）まで値として流れてしまう。想定する例外型に絞る
- 型注釈は `Result[dict, Exception]`。`exceptions=(ValueError,)` を付けたときだけ `Result[dict, ValueError]` に狭まる

## Test

`examples/result-try-to-result_test.py`
