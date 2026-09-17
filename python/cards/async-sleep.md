---
id: async-sleep
lang: python
title: 指定ミリ秒待つ
tags: [待機, スリープ, 遅延, 一時停止, sleep, delay, wait]
lib: stdlib
fn: asyncio.sleep
since: "3.7"
verified: 2026-09-17
status: public
---

指定秒数だけ現在のコルーチンを中断し、その間ほかのタスクにイベントループを譲る。ポーリング間隔やリトライ前の待機、テストのタイミング調整に使う。

## Signature

```python
asyncio.sleep(delay, result=None)
```

## Usage

```python
import asyncio

async def main() -> None:
    await asyncio.sleep(0.5)  # 0.5 秒待つ（他のタスクは動き続ける）
    task = asyncio.create_task(asyncio.sleep(10))
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")  # キャンセルは CancelledError として伝播する
asyncio.run(main())
```

## Contract

- `delay` 秒後に `result`（既定は `None`）を返す。待っている間はイベントループを止めず、ほかのタスクが実行される
- `delay` が `0` 以下なら実時間の待機はせず、イベントループに制御を 1 回だけ譲ってすぐ戻る。負数でも例外にならない
- 待機中にタスクがキャンセルされると、待機を打ち切って `asyncio.CancelledError` を送出する。`result` は返さない
- `delay` は数値であること。文字列や `None` を渡すと `TypeError` になる

## Alternatives

- 制限時間付きで別の非同期処理を待つなら `asyncio.timeout`（カード async-timeout）
- 同期コード（スレッド）で待つなら `time.sleep`。非同期コードの中では使わない
- 単にほかのタスクへ順番を譲りたいだけなら `asyncio.sleep(0)`

## Pitfalls

- 引数は **秒**。es-toolkit の `delay` はミリ秒なので `delay(500)` の移植は `sleep(0.5)`
- `time.sleep` を `async def` の中で呼ぶとイベントループごと止まり、すべてのタスクが待たされる。必ず `await asyncio.sleep`
- `await` を付け忘れるとコルーチンが作られるだけで待たない（`RuntimeWarning: coroutine 'sleep' was never awaited`）
- `AbortSignal` に相当する引数は無い。途中で止めるにはタスクにして `cancel()` する

## Test

`examples/async-sleep_test.py`
