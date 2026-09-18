---
id: log-structured
lang: python
title: ログを 1 行 1 JSON で出力する
tags: [構造化ログ, JSON ログ, ログ出力, 例外のログ, structured-logging, json-lines, logging, Formatter]
lib: stdlib
fn: logging.Formatter
since: "3.0"
verified: 2026-09-17
status: public
---

`logging.Formatter` を継承して `format` が JSON 文字列を返すようにし、ハンドラに付ける。ログ基盤（CloudWatch / Datadog / Loki など）で検索・集計できる形にするために使う。

## Signature

```python
class JsonFormatter(logging.Formatter): def format(self, record: logging.LogRecord) -> str
```

## Usage

```python
import json, logging
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
                 "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        if record.exc_info: entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)
# handler.setFormatter(JsonFormatter()) => {"time": "2026-09-17T14:00:00.000+00:00", "level": "INFO", "logger": "app", "msg": "GET / 200"}
```

## Contract

- `format` が返した文字列を `StreamHandler` がそのまま書き、末尾に `terminator`（既定 `'\n'`）を付ける。`json.dumps` はメッセージ中の改行を `\n` にエスケープするので 1 行 1 JSON が保たれる
- `record.getMessage()` は `msg % args` を適用した文字列。`record.msg` は書式文字列のまま（`logger.info("GET %s %d", path, status)` の `"GET %s %d"`）
- `record.created` は epoch 秒（`float`）。`datetime.fromtimestamp(record.created, timezone.utc)` で aware な UTC になり、`isoformat()` は `+00:00` 付き（`Z` ではない）
- `logger.exception(...)` / `exc_info=True` のとき `record.exc_info` に `(型, 例外, traceback)` が入る。`self.formatException(record.exc_info)` は `'Traceback (most recent call last):'` から始まる複数行の文字列で、`__cause__` の連鎖も含む
- `extra={"user_id": 7}` は `record.user_id` として属性になる。`msg` / `args` / `name` など `LogRecord` 既存の属性名と衝突すると `KeyError("Attempt to overwrite 'msg' in LogRecord")`
- `json.dumps` は `datetime` / `set` / 独自クラスで `TypeError`。`default=str` を付けないと `format` が失敗し、`Handler.handleError` が **stderr に `--- Logging error ---` を出す**（例外は呼び出し元に伝わらず、そのログは失われる）

## Alternatives

- `extra` の値をすべて出したいなら `LogRecord` の標準属性名の集合を除いた `record.__dict__` を `entry.update(...)` する（Test に例）
- 本番では `python-json-logger`（`JsonFormatter` を提供）や `structlog`（`structlog.processors.JSONRenderer`）
- 秘密情報をマスクしてから出すのはカード log-redact-secrets、リクエスト ID を自動で付けるのはカード log-correlation-id

## Pitfalls

- TypeScript 版は `JSON.stringify` に replacer で `Error` を展開するが、Python は `logger.exception` / `exc_info=True` で `record.exc_info` に例外が乗るので、`formatException` で文字列にする。`extra={"err": err}` に例外を入れても `default=str` で `str(err)` になるだけで traceback は出ない
- `logger.info(f"GET {path}")` と f-string で埋め込むと `record.args` が空になり、フィルタでの引数の加工（マスクなど）ができない。`logger.info("GET %s", path)` の遅延書式にする
- `json.dumps` の既定は `ensure_ascii=True` で日本語が `日本` になる。ログ基盤で読める形にするなら `ensure_ascii=False`
- `isoformat()` は `+00:00`。`Z` を要求するパーサーには `.replace("+00:00", "Z")` するか `strftime("%Y-%m-%dT%H:%M:%S.%fZ")` にする
- ルートロガーに `basicConfig` の既定 Formatter が残っていると、同じレコードが `%(message)s` 形式でも出て 2 重になる。ハンドラを差し替えるか `propagate = False` にする

## Test

`examples/log-structured_test.py`
