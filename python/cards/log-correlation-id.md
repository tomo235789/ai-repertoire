---
id: log-correlation-id
lang: python
title: リクエスト ID を非同期処理の連鎖に引き回す
tags: [リクエスト ID, 相関 ID, トレース, コンテキスト伝搬, correlation-id, request-id, contextvars, ContextVar]
lib: stdlib
fn: contextvars.ContextVar
since: "3.7"
verified: 2026-09-17
status: public
---

`ContextVar` に入れた値は、そのタスクと、そこから `create_task` したタスクの中で `await` をいくつ挟んでも `get()` で読める。引数で引き回さずにログへリクエスト ID を付けるために使う。

## Signature

```python
contextvars.ContextVar(name, *, default=...)  # .get([default]) / .set(value) -> Token / .reset(token)
```

## Usage

```python
import logging
from contextvars import ContextVar

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()  # => "req-1"（set したタスク内）/ None（外）。%(request_id)s で出せる
        return True
token = request_id.set("req-1")  # リクエスト開始時。await や create_task をまたいでも同じ値が見える
request_id.reset(token)           # リクエスト終了時に元へ戻す
```

## Contract

- `get()` は現在のコンテキストの値、未設定なら `default`。`default` 無しで未設定なら `LookupError`。`get(fallback)` で引数側の既定値も使える
- `set(value)` は `Token` を返し、`reset(token)` で **set 前の値** に戻す。同じ `Token` を 2 回 `reset` すると `RuntimeError`
- `asyncio.create_task` / `gather` / `TaskGroup` で作られたタスクは **作成時点のコンテキストのコピー** を持つ。タスクの中で `set` しても親や兄弟には影響せず、親がその後 `set` してもタスクには見えない
- 同じタスクの中で `await coro()` と直接待った場合はコンテキストを共有する。呼んだ先で `set` すると呼び元にも見える（`reset` しなければ残る）
- `threading.Thread` / `ThreadPoolExecutor.submit` / `loop.run_in_executor` で動く関数には **伝播せず** `default` に戻る。`contextvars.copy_context().run(fn)` を渡せばそのスレッドで同じ値が見える。`asyncio.to_thread` は内部で `copy_context` するので伝播する
- `logging.Filter` で `record.request_id = request_id.get()` を付ければ `Formatter` の `%(request_id)s` で出せる。ハンドラに `addFilter` すれば全ロガーのレコードに付く

## Alternatives

- HTTP サーバーならミドルウェアで `request_id.set(request.headers.get("x-request-id") or uuid.uuid4().hex)` し、`finally` で `reset`（FastAPI / Starlette は `asgi-correlation-id` パッケージが同じことをする）
- 分散トレースまで要るなら OpenTelemetry（`context` API は内部で `ContextVar` を使う）
- 複数の値を持たせるなら `ContextVar[dict]` にせず、値ごとに `ContextVar` を分ける（辞書を共有すると `set` 無しの変更が他タスクに漏れる）

## Pitfalls

- TypeScript の `AsyncLocalStorage.run(store, fn)` は `fn` の範囲で自動的に元へ戻るが、Python の `set` は **戻さない**。`try/finally` で `reset(token)` するか、`copy_context().run(handler)` で処理全体を包む
- `set` した値が `dict` などの可変オブジェクトだと、タスク間でコピーされるのは参照。中を変更すると別のタスクにも見える
- `reset` を忘れたワーカー（1 つのタスクで複数リクエストを順に処理するキュー消費など）は前のリクエストの ID を引きずる
- `run_in_executor` / `ThreadPoolExecutor` に渡した関数の中でログを出すと ID が `None` になる。`copy_context().run` で包むか `asyncio.to_thread` を使う
- モジュール直下で作った `ContextVar` を関数の中で作り直すと別の変数になる。1 か所で定義して import する

## Test

`examples/log-correlation-id_test.py`
