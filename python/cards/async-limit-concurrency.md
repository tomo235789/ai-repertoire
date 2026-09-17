---
id: async-limit-concurrency
lang: python
title: 非同期処理の同時実行数を制限する
tags: [同時実行数, 並列制限, セマフォ, 排他, concurrency-limit, semaphore, throttle-parallel, rate-limit]
lib: stdlib
fn: asyncio.Semaphore
since: "3.7"
verified: 2026-09-17
status: public
---

同時に走らせる非同期処理の数を `value` までに抑える。API のレート制限やコネクション数の上限に合わせて並列度を絞るのに使う。

## Signature

```python
asyncio.Semaphore(value=1)
```

## Usage

```python
import asyncio

sem = asyncio.Semaphore(2)  # 同時に 2 つまで

async def fetch_limited(item_id: int) -> dict:
    async with sem:  # 空きが出るまで待ち、ブロックを抜けるときに必ず解放する
        return await fetch_json(f"/api/items/{item_id}")

results = await asyncio.gather(*(fetch_limited(i) for i in range(1, 5)))
# => 常に 2 件以下しか同時に fetch されない
```

## Contract

- `async with sem:` はブロックに入るときに `acquire()`、抜けるときに `release()` する。ブロックの中で例外が出ても解放される
- `acquire()` は空きがあれば内部カウンタを 1 減らして即座に戻る。空きが無ければ `release()` が呼ばれるまで待つ
- CPython の実装では待機は `acquire()` を呼んだ順に解放されるが、ドキュメント上の保証ではない。再開順に依存するロジックを書かない
- `release()` はカウンタを 1 増やす。初期値を超えても例外にならず、その分だけ同時実行数が増える
- `locked()` は空きが無い（カウンタ 0）とき `True`
- 待機中の `acquire()` がキャンセルされると `CancelledError` になり、permit は取得しない
- 初期値に負数を渡すと `ValueError`

## Alternatives

- 余分な `release()` を `ValueError` で検出したいなら `asyncio.BoundedSemaphore(value)`
- 同時に 1 つだけ（排他）なら `asyncio.Lock`
- 3.11+ でタスクの集合を扱うなら `asyncio.TaskGroup` の中で `async with sem:` を組み合わせる
- 依存を増やせない場合は `itertools.batched`（3.12+）で分けて `asyncio.gather` を順に回す（バッチ内は並列、バッチ間は直列）

## Pitfalls

- `acquire()` / `release()` を手で書くと例外時の解放を忘れる。必ず `async with sem:` を使う
- es-toolkit の `Semaphore` は余分な `release()` を無視するが、`asyncio.Semaphore` は **カウンタを増やして上限が崩れる**。対応関係が不安なら `BoundedSemaphore`
- 待機が発生した時点でその時のイベントループに紐づく。モジュール変数として作った `Semaphore` を別の `asyncio.run()` から使うと `RuntimeError: ... is bound to a different event loop` になる
- 待機に制限時間は無い。必要なら `asyncio.timeout`（カード async-timeout）で `async with sem:` ごと包む

## Test

`examples/async-limit-concurrency_test.py`
