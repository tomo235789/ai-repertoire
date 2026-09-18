---
id: log-redact-secrets
lang: python
title: ログから秘密情報をマスクする
tags: [秘密情報のマスク, 機密情報, パスワード, トークン, redact, mask, sensitive-data, secrets]
lib: stdlib
fn: 純粋関数
since: "3.0"
verified: 2026-09-17
status: public
---

辞書を再帰的に辿り、`password` / `token` / `authorization` などのキーに入っている値を `"[REDACTED]"` に置き換えた新しい辞書を返す純粋関数。ログや例外レポートに秘密情報が混ざらないようにするために使う。

## Signature

```python
def redact(obj: Any, keys: Iterable[str] = ..., mask: str = "[REDACTED]") -> Any
```

## Usage

```python
def redact(obj, keys=("password", "token", "authorization", "secret", "api_key", "cookie"), mask="[REDACTED]"):
    lower = {k.lower() for k in keys}  # ジェネレータでも 1 度だけ実体化する
    def walk(v):
        if isinstance(v, dict):
            return {k: mask if str(k).lower() in lower else walk(x) for k, x in v.items()}
        return [walk(x) for x in v] if isinstance(v, list) else v
    return walk(obj)
redact({"user": "a", "password": "p", "headers": {"Authorization": "Bearer x"}, "items": [{"token": "t"}]})
# => {'user': 'a', 'password': '[REDACTED]', 'headers': {'Authorization': '[REDACTED]'}, 'items': [{'token': '[REDACTED]'}]}
```

## Contract

- キー名の一致は **大文字小文字を無視** して比較する（`Authorization` / `authorization` / `AUTHORIZATION` はすべて一致）。部分一致はしない（`password_hash` は `password` に一致しない）。キーが `str` でなければ `str(k)` で比較する
- 一致したキーの値は型を問わず `mask` に置き換える（辞書やリストでも丸ごと）。`None` の値も置き換える
- 純粋関数で、入力を変更しない。`dict` と `list` は新しいオブジェクトを返し（ネストした辞書も別オブジェクト）、それ以外（`str` / `int` / `tuple` / `datetime` / クラスインスタンス）は **中を辿らず同じオブジェクトをそのまま** 返す
- ネストの深さに制限はなく、リストの中の辞書・辞書の中のリストも辿る。循環参照があると `RecursionError`
- `keys` が空なら何も置き換えず、構造だけコピーして返す
- 戻り値の型は入力の形を保つが、マスク位置の値は `str` になる。マスクした辞書を処理に使わず、ログ直前だけに使う

## Alternatives

- `logging.Filter` に組み込むなら `record.args` を書き換える。`logger.info("login %s", data)` のように辞書を 1 つだけ渡すと `record.args` は **その辞書自体** なので `redact(record.args)`、複数ならタプルの各要素に適用する（Test に例）
- `dataclass` / pydantic モデルは `dataclasses.asdict` / `model_dump()` で辞書にしてから渡す
- 値の内容で判定（`Bearer ...` や 16 桁のカード番号）したいなら `re.sub` で文字列側を置換する。キー名ベースとは別物

## Pitfalls

- TypeScript 版はプレーンオブジェクトだけを辿るが、Python 版は `dict` と `list` だけ。`tuple` / `set` / `namedtuple` の中の辞書は辿らないので、必要なら `isinstance(obj, (list, tuple))` を足して同じ型で返す
- キー名は API や環境ごとに違う（`pass` / `pwd` / `x-api-key` / `client_secret` / `refresh_token`）。一覧は用途ごとに見直す
- 文字列の中に埋め込まれた秘密（URL の `?token=...`、`Authorization: Bearer ...` の 1 行）はキー名では見つからない。URL は `urllib.parse` で分解するか、正規表現で別途処理する
- 例外オブジェクト（`err.args`）や `httpx.Headers` は辞書ではない。`dict(response.headers)` などプレーンな辞書にしてから渡す
- `logger.info(f"login {data}")` と f-string で埋め込むと `record.args` が空で、フィルタでのマスクが効かない。遅延書式（`%s`）で渡す

## Test

`examples/log-redact-secrets_test.py`
