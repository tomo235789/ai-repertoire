---
id: http-timeout
lang: python
title: HTTP リクエストに制限時間を設ける
tags: [HTTP タイムアウト, 制限時間, 接続タイムアウト, 読み取りタイムアウト, timeout, httpx, deadline, ReadTimeout]
lib: httpx
fn: Timeout
since: "0.27"
verified: 2026-09-17
status: public
---

`httpx.Timeout(5.0, connect=2.0)` を `timeout=` に渡し、接続に 2 秒、以降の各操作に 5 秒の上限を付ける。超えたら `httpx.TimeoutException` のサブクラスを投げる。応答しないサーバーで待ち続けないために使う。

## Signature

```python
httpx.Timeout(timeout=..., *, connect=..., read=..., write=..., pool=...)
```

## Usage

```python
import httpx

try:
    r = httpx.get("https://example.com/items", timeout=httpx.Timeout(5.0, connect=2.0))
    data = r.json()  # 本文はここまでに読み終わっている（ストリーミングでなければ）
except httpx.TimeoutException as err:  # ConnectTimeout / ReadTimeout / WriteTimeout / PoolTimeout の基底
    print(f"制限時間内に終わらなかった: {type(err).__name__}")
# httpx.get(url, timeout=None)  # 無制限。省略すると既定の 5 秒
```

## Contract

- `Timeout(5.0)` は `connect` / `read` / `write` / `pool` の 4 つ全部を 5 秒にする。`Timeout(5.0, connect=2.0)` は `connect` だけ上書き。既定値なしで一部だけ指定（`Timeout(connect=2.0)`）は `ValueError`
- `timeout=` を省略すると **既定で 5 秒**（`httpx.Client().timeout` は `Timeout(timeout=5.0)`）。`timeout=None` で無制限。`float` / `int` を直接渡すと `Timeout(値)` と同じ
- `read` は「次のデータが届くまで」の待ち時間で、リクエスト全体の合計ではない。ヘッダー到着後、本文の途中で `read` 秒止まっても `ReadTimeout` になる
- 超過したときの例外は `ConnectTimeout` / `ReadTimeout` / `WriteTimeout` / `PoolTimeout`。すべて `httpx.TimeoutException` → `httpx.TransportError` のサブクラスで、`str(err)` は `'timed out'`
- 接続拒否は `httpx.ConnectError`（`TimeoutException` ではない）。サーバーが 4xx / 5xx を返した場合は例外にならず `Response` が返る
- `httpx.Client(timeout=...)` で既定を決め、`client.get(url, timeout=...)` でリクエストごとに上書きできる

## Alternatives

- 標準ライブラリだけなら `urllib.request.urlopen(url, timeout=5.0)`。超過時は組み込みの `TimeoutError`（接続時は `URLError` に包まれる）
- 「全体で N 秒」を保証したいなら非同期にして `async with asyncio.timeout(N): await client.get(...)`（カード async-timeout）
- 待ちすぎたら再試行するならカード http-retry-idempotent（`ReadTimeout` も `TransportError` なので同じ判定で拾える）

## Pitfalls

- TypeScript の `AbortSignal.timeout(ms)` は接続から本文読み終わりまで **通しで** 数えるが、httpx の `read` は **データが届かない区間ごと** に数える。少しずつ届き続ける遅いレスポンスはいつまでも終わらない。全体の上限が要るなら `asyncio.timeout` を外側に付ける
- 既定の 5 秒に頼ると、大きなレスポンスや遅い API で `ReadTimeout` になる。用途ごとに明示する
- `except httpx.TimeoutException` を `except httpx.ReadTimeout` にすると `ConnectTimeout` を取りこぼす。区別が要らなければ基底で受ける
- `Timeout(connect=2.0)` のように既定値を省くと `ValueError`。4 つ全部書くか、先頭に既定値を置く
- `requests` の `timeout=(connect, read)` タプルは httpx では使えない。`httpx.Timeout(read, connect=connect)` に書き換える

## Test

`examples/http-timeout_test.py`
