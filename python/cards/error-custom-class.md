---
id: error-custom-class
lang: python
title: 独自のエラー型を定義する
tags: [独自エラー, 例外クラス, 例外の種類分け, 継承, custom-exception, class, Exception, args]
lib: stdlib
fn: Exception
since: "3.0"
verified: 2026-09-17
status: public
---

`Exception` を継承したクラスに固有の属性を持たせ、`except` / `isinstance` で種類を判定できるようにする。アプリ用の基底クラスを 1 つ置き、その下に具体的な例外を並べる。

## Signature

```python
class NotFoundError(AppError): def __init__(self, key: str) -> None: super().__init__(key); self.key = key
```

## Usage

```python
class AppError(Exception):
    """アプリ内の例外の基底。呼び出し側は except AppError で全部拾える"""

class NotFoundError(AppError):
    def __init__(self, key: str) -> None:
        super().__init__(key)   # args に引数をそのまま残す（pickle / repr のため）
        self.key = key
    def __str__(self) -> str:
        return f"not found: {self.key}"
raise NotFoundError("user:1")  # => NotFoundError: not found: user:1（traceback の最終行）
```

## Contract

- `super().__init__(*args)` に渡した値が `e.args`（タプル）になる。`str(e)` は既定で `args` が 0 個なら `''`、1 個なら `str(args[0])`、2 個以上なら `str(args)`。`repr(e)` は `型名(*args)` の形
- traceback の最終行と `traceback.format_exception_only(e)` は `型名: str(e)`（`__main__` と組み込み以外のクラスは `モジュール名.型名`）。`__str__` を上書きすればそこに反映される。クラス名は自動で使われ、TypeScript のように `name` を代入する必要はない
- `except AppError` はサブクラスも捕捉する。`except NotFoundError` を先に書けば個別に処理でき、複数なら `except (NotFoundError, PermissionError)`
- `pickle` / `copy` は `type(e)(*e.args)` で作り直してから `__dict__` を復元する。`__init__` の引数と `args` がずれていると（`super().__init__(f"not found: {key}")` のようにメッセージだけ渡す）、復元後の `args` と `str(e)` がメッセージの二重（`not found: not found: user:1`）になる。引数の数が違えば `TypeError`
- `super().__init__()` を呼ばなくても `args` はコンストラクタの引数から自動で設定される（`BaseException.__new__` が保存する）。呼ぶのは明示のため
- 引数が必須な例外は `raise NotFoundError` のようにクラスだけで投げると `TypeError`。必ずインスタンスを作る
- `e.add_note("while loading config")`（3.11）で後から文脈を足せる。`__notes__` に溜まり traceback に表示される

## Alternatives

- 属性が多いなら `@dataclass` を付ける（`class E(Exception)` に `@dataclass(frozen=True)` は不可。`eq=False` を付けて `__hash__` を守る）
- 原因の例外を持たせて包み直すのはカード error-cause-chain（`raise NotFoundError(key) from err`）
- HTTP ステータスなどの分類はクラス属性 `status = 404` にして、基底クラス側で `self.status` を読む

## Pitfalls

- TypeScript は `this.name = 'HttpError'` を書かないと `'Error'` のままだが、Python は `type(e).__name__` が自動で使われる。逆に `json.dumps(e)` は `TypeError` になるので、ログには `str(e)` と `e.args` / 属性を明示的に出す（カード log-structured）
- `super().__init__(f"...")` でメッセージだけ渡すと `pickle` 越し（`multiprocessing` / `concurrent.futures.ProcessPoolExecutor`）でメッセージが壊れる。`args` にはコンストラクタの引数をそのまま残し、表示は `__str__` で作る
- `class ValidationError(Exception): pass` だけでも動くが、属性が無いと呼び出し側が `str(e)` を解析することになる。構造化したい値は属性に持たせる
- `except Exception` は `KeyboardInterrupt` / `SystemExit` を通す（`BaseException` 直下）。それ以外は全部拾うので、アプリの例外は `AppError` で受けてバグ（`TypeError` など）と分ける
- 例外クラスの `__eq__` は同一性。`NotFoundError("a") == NotFoundError("a")` は `False`。テストでは `type` と `args` / 属性で比較する

## Test

`examples/error-custom-class_test.py`
