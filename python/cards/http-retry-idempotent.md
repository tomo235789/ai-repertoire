---
id: http-retry-idempotent
lang: python
title: 冪等な HTTP リクエストを再試行する
tags: [HTTP 再試行, リトライ, 冪等, サーバーエラー, retry, idempotent, httpx, 5xx]
lib: tenacity
fn: retry
since: "9.0"
verified: 2026-09-17
status: public
---

httpx の呼び出しを `tenacity.retry` で包み、通信エラー（`TransportError`）と 5xx のレスポンスだけをやり直す。**冪等なリクエスト（GET / PUT / DELETE、または冪等キー付き POST）に限る**。

## Signature

```python
@tenacity.retry(retry=retry_if_exception_type(...) | retry_if_result(...), stop=..., wait=..., reraise=False)
```

## Usage

```python
import httpx
from tenacity import retry, retry_if_exception_type, retry_if_result, stop_after_attempt, wait_exponential

@retry(
    retry=retry_if_exception_type(httpx.TransportError) | retry_if_result(lambda r: r.status_code >= 500),
    stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.5, max=10), reraise=True,
)
def get_item(client: httpx.Client) -> httpx.Response:
    return client.get("https://example.com/items/1")
# => 5xx 未満の Response。4xx は 1 回で返る。5xx / 通信エラーが 4 回続いたら RetryError / 最後の例外
```

## Contract

- httpx はレスポンスが届けば **ステータスに関わらず `Response` を返す**（`raise_for_status()` を呼ぶまで例外にならない）。5xx を再試行させるには `retry_if_result` で `status_code` を見る
- 接続拒否・DNS 失敗・タイムアウトは `httpx.TransportError`（`ConnectError` / `ReadTimeout` などの基底）。`retry_if_exception_type(httpx.TransportError)` で拾える。`HTTPStatusError` は `TransportError` のサブクラスではない
- `retry_if_exception_type(...) | retry_if_result(...)` は **どちらかが真なら再試行**。`retry_if_result` の述語には `Response` が渡り、`status_code >= 500` が偽（2xx〜4xx）ならその `Response` をそのまま返して終わる
- `stop_after_attempt(4)` は初回を含む合計 4 回。使い切ったときは `tenacity.RetryError`。`reraise=True` を付けても、最後の試行が **例外** なら元の例外（`ReadTimeout` など）、**5xx のレスポンス** なら `RetryError`（`err.last_attempt.result()` がその `Response`）
- 試行ごとに `client.get(...)` を呼び直すので、`Request` の使い回しは不要。本文を `bytes` / `dict`（`json=`）で渡していれば毎回同じ本文が送られる
- `wait` を省略すると待たずに連打する。`wait_exponential` か `wait_exponential_jitter` を必ず付ける

## Alternatives

- 429 / 503 の `Retry-After` を尊重した指数バックオフはカード http-rate-limit-backoff
- 1 回ごとに制限時間を付けるなら `client.get(url, timeout=httpx.Timeout(...))`（カード http-timeout）を関数の中に書く
- 接続レベルの再試行だけなら `httpx.HTTPTransport(retries=3)`（接続確立の失敗のみ。レスポンスは見ない）

## Pitfalls

- TypeScript（`fetch`）は接続失敗を `TypeError` で reject するが、httpx は `TransportError` を投げる。`except Exception` で拾うと `HTTPStatusError` やバグまで再試行してしまうので型を絞る
- 冪等でない POST（注文・送金・投稿）を再試行すると **二重実行** になる。サーバーが冪等キー（`Idempotency-Key` ヘッダなど）を受け付ける場合だけ再試行する
- 「送信前に切れた」のか「サーバーが処理したあとに切れた」のかは `TransportError` からは区別できない。冪等性はサーバー側で担保する
- 4xx（特に 401 / 403 / 404 / 422）を再試行しても結果は変わらない。`408`（Request Timeout）だけは再試行してよい
- `stream=True` / `content=` にイテレータを渡したリクエストは 2 回目に本文を送れない。試行ごとに本文を作り直す

## Test

`examples/http-retry-idempotent_test.py`
