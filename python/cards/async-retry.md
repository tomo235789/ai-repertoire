---
id: async-retry
lang: python
title: 失敗した非同期処理を再試行する
tags: [再試行, リトライ, 失敗時の再実行, バックオフ, retry, backoff, resilience]
lib: tenacity
fn: tenacity.retry
since: "9.0"
verified: 2026-09-17
status: public
---

関数が例外を投げたら待って再実行し、成功した値を返すデコレータ。一時的なネットワークエラーへの対処に使う。同期関数にも `async def` にも同じ書き方で付けられる。

## Signature

```python
@tenacity.retry(stop=..., wait=..., retry=..., reraise=False, before_sleep=None)
```

## Usage

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(4),                      # 合計 4 回まで試す
    wait=wait_exponential(multiplier=0.1, max=1),    # 0.1, 0.2, 0.4 秒の指数バックオフ
    retry=retry_if_exception_type(ConnectionError),  # この例外のときだけ再試行
    reraise=True,                                    # 使い切ったら元の例外を投げる
)
async def fetch_items() -> list[dict]:
    return await fetch_json("/api/items")  # => 成功した回の値。4 回とも失敗したら最後の ConnectionError
```

## Contract

- 関数を呼び、例外が出たら `wait` だけ待って再実行する。正常に返った時点でその値を返す
- `stop_after_attempt(n)` は **合計の試行回数**（初回を含む）。`stop` を省略すると成功するまで無限に試す
- `retry` を省略すると `Exception` のサブクラスすべてを再試行する。`retry_if_exception_type(...)` に合わない例外は再試行せず、その場でそのまま投げる。`KeyboardInterrupt` などの `BaseException` は捕捉しない
- 上限に達したときは既定で `tenacity.RetryError` を投げる。元の例外は `err.last_attempt.exception()` から取り出す。`reraise=True` なら **最後の試行の元の例外** をそのまま投げる
- `wait` は `wait_fixed(sec)` / `wait_exponential(...)` などのオブジェクト。省略すると待たない。最後の試行のあとには待たない
- `before_sleep=callback` は再試行の待機に入る前に毎回呼ばれ、`RetryCallState` から `attempt_number` / `outcome.exception()` / `next_action.sleep` を読める
- `async def` に付けると装飾後も `async def` のままで、待機は `asyncio.sleep` で行われイベントループを止めない。同期関数では `time.sleep` で待つ

## Alternatives

- 1 回ごとに制限時間も付けたいなら関数の中で `asyncio.timeout`（カード async-timeout）を組み合わせる
- 使い切ったとき例外ではなく既定値を返したいなら `retry_error_callback=lambda state: default`
- 同じ設定を別の関数に使い回すなら `Retrying(...)` / `AsyncRetrying(...)` を `for attempt in ...` で回す
- 依存を増やせない場合は `for` ループと `try/except` と `asyncio.sleep`（カード async-sleep）

## Pitfalls

- es-toolkit の `retry` は最後のエラーをそのまま投げるが、tenacity は既定で `RetryError` に包む。`except ConnectionError` で捕まえたいなら `reraise=True` を付ける
- `stop` を省略すると無限に再試行する。必ず `stop_after_attempt` か `stop_after_delay` を付ける
- `stop_after_attempt(3)` は「3 回再試行」ではなく「合計 3 回」。es-toolkit の `retries: 3`（合計 4 回）とは数え方が違う
- 冪等でない処理（送金・投稿）を再試行すると二重実行になる。`retry=` で送信前の例外だけに限定する
- 同期関数に付けた場合の `wait` は `time.sleep` で待つ。非同期コードから同期の装飾済み関数を呼ぶとイベントループが止まる

## Test

`examples/async-retry_test.py`
