---
id: function-once
lang: cpp
title: 関数を 1 回だけ実行する
tags: [一度だけ, 初期化, 遅延初期化, once, call-once, init, lazy-init, thread-safe]
lib: stdlib
fn: std::call_once
since: "C++11"
verified: 2026-09-17
status: public
---

`std::once_flag` と組にして、同じフラグに対する呼び出しのうち最初の 1 回だけ関数を実行する。複数スレッドから呼ばれても 1 回に限定される。設定の読み込みやクライアントの初期化に使う。

## Signature

```cpp
template<class Callable, class... Args> void std::call_once(std::once_flag& flag, Callable&& f, Args&&... args);
```

## Usage

```cpp
#include <mutex>

std::once_flag flag;
int config = 0;
int get_config() {
  std::call_once(flag, [] { config = 42; });  // 最初の呼び出しだけ実行される
  return config;
}
get_config();  // => 42（ここで初期化）
get_config();  // => 42（再実行されない）
```

## Contract

- 同じ `once_flag` に対する `call_once` は最初の 1 回だけ `f` を実行し、以後は `f` を呼ばずに戻る。別の関数を渡しても実行されない。返り値は無いので結果は自分で保持する
- 複数スレッドから同時に呼んでも実行は 1 回。他のスレッドは実行が終わるまで待ち、戻ったときには `f` の副作用が見える
- `args...` は `f` に転送される。2 回目以降の引数は無視される
- `f` が例外を投げると **未実行扱い** になる。規格の契約では例外は呼び出し元に伝播し、フラグは設定されず、次の `call_once` が `f` を再実行する（Linux の libstdc++ で確認）。ただし確認した実装のうち **macOS の Homebrew GCC 16.2 の libstdc++（futex が無く `pthread_once` ベース）では、例外の後の `call_once` が戻らず固まる**。規格どおりではない実装の不具合で、ヘッダにも "pthread_once does not reset the flag if an exception is thrown" とある
- `once_flag` はコピーもムーブもできない。`constexpr` の既定コンストラクタを持つ

## Alternatives

- 関数内の `static` 変数（マジックスタティック）: `static const Config c = load();`。初期化はスレッド安全に 1 回だけ行われ、値を返せる。初期化中に例外が投げられると未初期化のままで次の呼び出しが再試行する（この挙動は macOS でも確認）。フラグと結果を別に持つ必要が無いので、まずこちらを検討する
- 引数ごとに結果を使い回したいなら function-memoize
- 「最初の 1 回だけ」ではなく排他が欲しいなら `std::mutex` + `std::lock_guard`

## Pitfalls

- 例外時の挙動が言語で違う。TypeScript（es-toolkit の `once`）は例外を投げても「実行済み」にするが、Python の `functools.cache` と C++ の `call_once` は再試行する。さらに確認した実装のうち macOS の Homebrew GCC 16.2 の libstdc++ では規格に反して例外後に固まる。失敗し得る初期化は `call_once` の中で例外を捕まえて結果を状態として保存するか、マジックスタティックを使う
- `call_once` は値を返さない。ラムダで外の変数に代入する
- `once_flag` を関数のローカル変数にすると呼び出しごとに新しいフラグになり毎回実行される。`static` かクラスのメンバとして持つ

## Test

`examples/function-once_test.cpp`
