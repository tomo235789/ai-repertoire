---
id: function-memoize
lang: python
title: 関数の戻り値を引数ごとにキャッシュする
tags: [メモ化, キャッシュ, 計算結果の再利用, memoize, memoization, cache, memo]
lib: stdlib
fn: functools.cache
since: "3.9"
verified: 2026-09-17
status: public
---

同じ引数での呼び出し結果をキャッシュし、2 回目以降は関数を実行せずに返す。重い純粋関数（パース・集計・正規化）の再計算を避けるのに使う。

## Signature

```python
@functools.cache
```

## Usage

```python
from functools import cache

@cache
def area(r: float) -> float:
    print("calc")
    return 3.14159 * r * r

area(2)  # 'calc' が出て 12.56636
area(2)  # キャッシュから 12.56636（'calc' は出ない）
area.cache_info()  # => CacheInfo(hits=1, misses=1, maxsize=None, currsize=1)
```

## Contract

- キャッシュキーは **すべての引数**（位置引数とキーワード引数）から作る。キーが同じなら関数を呼ばず保存した戻り値をそのまま返す
- 位置で渡すかキーワードで渡すか、キーワード引数の順序が違うと別キーになることがある（`f(1, 2)` / `f(1, b=2)` / `f(b=2, a=1)`。仕様上は「別エントリになり得る」で、CPython では別キー）
- 引数はすべて hashable であること。`list` や `dict` を渡すと `TypeError: unhashable type` になる
- キャッシュに無いときだけ関数を呼び、戻り値を保存してから返す。関数が例外を投げた場合は保存しない（次回また呼ばれる）
- `cache_info()` で `hits` / `misses` / `currsize` を確認でき、`cache_clear()` で全消去できる。上限は無く `maxsize=None`
- 複数スレッドから同時に呼ぶと、保存前の呼び出しが重なって関数が複数回実行されることがある（結果の保存自体は壊れない）

## Alternatives

- サイズ上限が要るなら `functools.lru_cache(maxsize=128)`（`cache` は `lru_cache(maxsize=None)` と同じ）
- 引数無しの初期化を 1 回だけ走らせたいなら `cache` を引数無しの関数に付ける（カード function-once）
- インスタンスごとに 1 回だけ計算する属性なら `functools.cached_property`（インスタンスの `__dict__` に保存されるのでメモリリークにならない）
- TTL や非同期関数の対応が要るなら `cachetools` / `async_lru`

## Pitfalls

- es-toolkit の `memoize` は第 1 引数だけをキーにするが、`cache` は全引数をキーにする。第 2 引数以降を変えると別キーになる
- 引数が unhashable な関数には付けられない。`list` はタプルに、`dict` は `frozenset(d.items())` に変換してから渡す
- メソッドに付けると `self` もキーに含まれ、インスタンスがキャッシュから参照され続けて解放されない（メモリリーク）。`cached_property` か、インスタンスに依存しない静的関数に切り出す
- キャッシュは無制限に増える。ユーザー入力など値域が広い引数をキーにするなら `lru_cache(maxsize)` にする
- 非純粋な関数（時刻や乱数、外部状態に依存）に付けると古い値を返し続ける

## Test

`examples/function-memoize_test.py`
