---
id: http-rate-limit-backoff
lang: python
title: レート制限に指数バックオフで対処する
tags: [レート制限, 指数バックオフ, 待って再試行, スロットリング, rate-limit, backoff, retry-after, "429"]
lib: tenacity
fn: wait_exponential_jitter
since: "9.0"
verified: 2026-09-17
status: public
---

429 / 503 を受けたら `Retry-After` ヘッダの秒数、無ければ `wait_exponential_jitter` の指数バックオフ + ジッターだけ待ってやり直す。API の呼び出し制限に当たったときに使う。

## Signature

```python
tenacity.wait_exponential_jitter(initial=1, max=..., exp_base=2, jitter=1)
```

## Usage

```python
from datetime import datetime; from email.utils import parsedate_to_datetime
from tenacity import RetryCallState, retry, retry_if_result, stop_after_delay, wait_exponential_jitter

def wait_retry_after(state: RetryCallState) -> float:  # Retry-After（秒数か HTTP-date）を優先
    h = state.outcome.result().headers.get("Retry-After") if state.outcome and not state.outcome.failed else None
    if h and h.strip().isdigit(): return float(h)
    if h and (w := parsedate_to_datetime(h)): return max(0.0, (w - datetime.now(w.tzinfo)).total_seconds())
    return wait_exponential_jitter(initial=1, max=30, jitter=1)(state)
# @retry(retry=retry_if_result(lambda r: r.status_code in (429, 503)), wait=wait_retry_after, stop=stop_after_delay(120))
# => 待ち時間: Retry-After 秒（過去日付なら 0）、無ければ 1, 2, 4, 8, 16, 30 … 秒 + 0〜1 秒のジッター
```

## Contract

- `wait_exponential_jitter(initial, max, exp_base, jitter)` の待ち時間は `min(initial * exp_base ** (attempt_number - 1) + uniform(0, jitter), max)`。`attempt_number` は 1 始まりなので 1 回目の待ちは `initial + ジッター`。`max` はジッターを足したあとに適用され、超えない
- `wait=` には `RetryCallState` を受けて秒数（`float`）を返す **任意の関数** を渡せる。`state.outcome` は直前の試行の結果で、`.failed` が `False` なら `.result()` が戻り値（ここでは `Response`）、`True` なら `.exception()`
- `Response.headers` は大文字小文字を区別しないので `headers.get("Retry-After")` で `retry-after` も取れる。値は秒数（`"3"`）か HTTP 日付（`"Wed, 21 Oct 2015 07:28:00 GMT"`）で、日付は `email.utils.parsedate_to_datetime` で `datetime` にできる
- `retry_if_result` で 429 / 503 に限定する。それ以外の 5xx や通信エラーはカード http-retry-idempotent の判定と `|` で組み合わせる
- `stop_after_delay(n)` は最初の試行からの **実経過秒**（`state.seconds_since_start`）が `n` 以上なら止める。試行回数ではなく総待ち時間で上限を決められる。使い切ると `RetryError`（`last_attempt.result()` が最後の `Response`）
- 待機は同期関数なら `time.sleep`、`async def` なら `asyncio.sleep`。`sleep=` 引数で差し替えられる（テストで待ち時間を記録するのに使う）

## Alternatives

- ジッターを乗せず素の指数バックオフなら `wait_exponential(multiplier=1, max=30)`。全体を乱数にする「フルジッター」は `wait_random_exponential(multiplier=1, max=30)`
- 制限に当たる前に送信間隔を制御するならトークンバケット（`aiolimiter` / `limits`）
- 複数リクエストを並列に送るなら `asyncio.Semaphore`（カード async-limit-concurrency）で同時数を絞る方が先

## Pitfalls

- TypeScript（es-toolkit）の `delay(attempts, error)` は 0 始まりだが、tenacity の `attempt_number` は 1 始まり。`exp_base ** (attempt_number - 1)` なので 1 回目が `initial` になる
- `Retry-After` が返っているのに指数バックオフで短く待つと、サーバーの指示より早く叩いて再度 429 になる。ヘッダを優先する
- `stop` を省略すると成功するまで無限に待つ。`stop_after_delay` か `stop_after_attempt` を必ず付ける
- `wait` に乱数が入るとテストが不安定になる。`jitter=0` を渡すか `sleep=` に記録関数を注入して待ち時間を検証する
- `stop_after_delay` は待機の途中では止めない。待ち時間 30 秒が上限 120 秒の直前に始まれば合計 150 秒近くになる

## Test

`examples/http-rate-limit-backoff_test.py`
