---
id: function-once
lang: python
title: 関数を 1 回だけ実行する
tags: [一度だけ, 初回のみ, 初期化, 遅延初期化, once, single-call, lazy-init]
lib: stdlib
fn: functools.cache
since: "3.9"
verified: 2026-09-17
status: public
---

引数無しの関数に `cache` を付けると、最初の呼び出しだけ関数を実行し、以後は最初の戻り値を返し続ける。設定の読み込みやクライアントの初期化を 1 回に限定するのに使う。

## Signature

```python
@functools.cache
```

## Usage

```python
from functools import cache

@cache
def load_config() -> dict[str, str]:
    print("load")
    return {"mode": "test"}

a = load_config()  # 'load' が出る
b = load_config()  # 何も出ない。a と同じオブジェクトが返る
a is b  # => True
```

## Contract

- 引数無しの関数に付けると、1 回目の呼び出しで関数を実行し戻り値を保存する。2 回目以降は関数を呼ばず **1 回目の戻り値（同じオブジェクト）** を返す
- 1 回目に関数が例外を投げた場合は「実行済み」にならず、例外がそのまま伝わる。2 回目の呼び出しで **再実行** され、成功すればその戻り値を保存する
- `cache_clear()` を呼ぶと未実行の状態に戻り、次の呼び出しで再実行される
- 複数スレッドから同時に呼ぶと、保存前の呼び出しが重なって関数が複数回実行されることがある。排他は保証されない
- 状態は装飾された関数ごとに持つ。元の関数は `__wrapped__` から呼べ、変更されない

## Alternatives

- 引数ごとに結果を使い回したいなら同じ `cache` を引数付きの関数に付ける（カード function-memoize）
- インスタンスごとに 1 回だけ計算する属性なら `functools.cached_property`
- 複数スレッドからの初期化を厳密に 1 回にしたいなら `threading.Lock` で二重チェックする自前の関数を書く
- 非同期の初期化を 1 回にしたいなら、`asyncio.Task` を作って保持する（`cache` を `async def` に付けるとコルーチンオブジェクトが共有され、2 回目の `await` で `RuntimeError` になる）

## Pitfalls

- es-toolkit の `once` は例外を投げた初期化も「実行済み」にするが、`cache` は例外を保存しないので **失敗した初期化は再試行される**。挙動が逆
- 引数を渡すと引数ごとに別々に 1 回ずつ実行される。「引数に関係なく 1 回」にはならない
- 戻り値は同じオブジェクトが共有されるので、呼び出し側で変更すると次の呼び出しにも影響する
- メソッドに付けると `self` ごとに 1 回になり、インスタンスがキャッシュから参照され続ける（カード function-memoize の Pitfalls と同じ）

## Test

`examples/function-once_test.py`
