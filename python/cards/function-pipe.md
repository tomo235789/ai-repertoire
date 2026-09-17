---
id: function-pipe
lang: python
title: 複数の関数を左から順に合成する
tags: [関数合成, パイプライン, 左から右, 合成, pipe, compose, flow]
lib: toolz
fn: toolz.pipe
since: "1.0"
verified: 2026-09-17
status: public
---

値を最初の関数に渡し、その結果を次の関数に渡す、を左から順に繰り返して最後の結果を返す。ネストした呼び出し `h(g(f(x)))` を読みやすい順に並べるのに使う。

## Signature

```python
toolz.pipe(data, *funcs)
```

## Usage

```python
from toolz import pipe

def double(n: int) -> int:
    return n * 2

def to_label(n: int) -> str:
    return f"total: {n}"

pipe(3, double, to_label)
# => 'total: 6'
```

## Contract

- `data` を最初の関数に渡し、以降の関数は直前の戻り値 1 つを受け取る。左から順に同期的に実行する
- 関数を 0 個で `pipe(data)` としたときは `data` をそのまま返す
- 各関数は引数 1 つで呼ばれる。2 つ以上の必須引数を持つ関数を渡すと `TypeError` になる
- 非同期関数を混ぜても `await` しない。コルーチンオブジェクトがそのまま次の関数に渡される
- 渡された関数を変更しない。実行するだけで新しい関数は作らない

## Alternatives

- 値を渡さずに合成した関数だけ作りたいなら `toolz.compose_left(f, g)`（`compose_left(f, g)(x)` は `pipe(x, f, g)` と同じ）。数学的な右から左の順なら `toolz.compose(g, f)`
- 複数の引数が要る関数は `functools.partial` で残り 1 つの引数にしてから渡す（`pipe(xs, partial(map, double), list)`）
- 依存を増やせない場合は `to_label(double(x))` と直接ネストするか、中間変数に代入して並べる
- 遅延評価のイテレータ処理が主なら `toolz.curried` の `map` / `filter` と組み合わせる

## Pitfalls

- es-toolkit の `flow` は合成した関数を返すが、`toolz.pipe` は **値を先に受け取ってその場で実行する**。関数を作りたいなら `compose_left`
- 非同期のステップを混ぜると 2 つ目以降がコルーチンオブジェクトを受け取って壊れる。非同期パイプラインは `async def` の中で `await` を並べる
- 2 番目以降の関数に複数の値を渡したいなら、直前の関数でタプルや辞書に束ねる

## Test

`examples/function-pipe_test.py`
