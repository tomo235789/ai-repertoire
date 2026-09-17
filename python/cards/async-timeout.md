---
id: async-timeout
lang: python
title: Promise に制限時間を設ける
tags: [タイムアウト, 制限時間, 打ち切り, 時間切れ, timeout, deadline, time-limit]
lib: stdlib
fn: asyncio.timeout
since: "3.11"
verified: 2026-09-17
status: public
---

`async with` ブロックの中の非同期処理が `delay` 秒以内に終わらなければ中の処理をキャンセルし、`TimeoutError` を送出する。外部 API 呼び出しの待ちすぎ防止に使う。

## Signature

```python
asyncio.timeout(delay)
```

## Usage

```python
import asyncio

async def main() -> None:
    try:
        async with asyncio.timeout(3):
            data = await fetch_json("/api/items")  # 3 秒以内に終わればそのまま続く
    except TimeoutError:
        print("3 秒以内に終わらなかった")

asyncio.run(main())
```

## Contract

- ブロックの中の `await` が `delay` 秒以内に終わらなければ、中の処理を **キャンセル** してから `TimeoutError` を送出する。ブロックの残りは実行されない
- `TimeoutError` は組み込みの `TimeoutError`（3.11 から `asyncio.TimeoutError` と同一）
- 時間内に終わればブロックの結果がそのまま使え、`expired()` は `False`。超過したときは `True`
- ブロックの中で投げられた `TimeoutError` 以外の例外はそのまま伝わる
- `delay` が `0` 以下でもブロックの中で `await` した時点で `TimeoutError` になる。`None` なら制限無し
- `reschedule(when)` で締め切り（`loop.time()` 基準の絶対時刻）を延長・短縮できる。`when()` で現在の締め切りを確認できる
- コンテキストマネージャは 1 回しか使えない。2 回目の `async with` は `RuntimeError`

## Alternatives

- 相対秒ではなく絶対時刻で指定するなら `asyncio.timeout_at(when)`
- 1 つのコルーチンだけに付けるなら `asyncio.wait_for(coro, timeout)`（超過時の挙動は同じで、キャンセルしてから `TimeoutError`）
- 3.10 以前は `async-timeout` パッケージの `async_timeout.timeout(delay)`

## Pitfalls

- es-toolkit の `withTimeout` はタイムアウトしても元の処理を止めないが、`asyncio.timeout` は中の処理を **キャンセルする**。途中で止まってはいけない処理（書き込み・送金など）を `asyncio.shield` で包んでも、待つ側は `TimeoutError` になり中の処理はバックグラウンドで続くだけなので、完了保証にはならない（再試行すると二重実行になる）。Task の参照を保持してタイムアウト後に結果を回収するか、キャンセル時の後始末を書く
- 中の処理が `CancelledError` を握りつぶすと `TimeoutError` にならず、ブロックが最後まで走ってしまう。`except CancelledError` の後は必ず `raise` する
- ブロックの外側でタスク自体がキャンセルされた場合は `TimeoutError` に変換されず `CancelledError` のまま伝わる
- 時間切れかどうかの判定は `except TimeoutError`。3.10 以前の `asyncio.TimeoutError` は別クラスだったので、古いコードを流用するときは注意する

## Test

`examples/async-timeout_test.py`
