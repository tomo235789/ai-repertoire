---
id: function-once
lang: rust
title: 関数を 1 回だけ実行する
tags: [一度だけ, 初回のみ, 初期化, 遅延初期化, once, single-call, lazy-init]
lib: stdlib
fn: std::sync::OnceLock
since: "1.70"
verified: 2026-09-17
status: public
---

`OnceLock` に初期化クロージャを渡すと、最初の `get_or_init` だけ実行して値を保存し、以後は同じ値への参照を返し続ける。設定の読み込みやクライアントの初期化を 1 回に限定するのに使う。スレッド安全で `static` に置ける。

## Signature

```rust
pub fn get_or_init<F>(&self, f: F) -> &T where F: FnOnce() -> T
```

## Usage

```rust
use std::sync::OnceLock;

static CONFIG: OnceLock<String> = OnceLock::new();

fn config() -> &'static str {
    CONFIG.get_or_init(|| { println!("load"); "mode=test".to_string() })
}
config(); // "load" と表示して "mode=test"
config(); // 何も表示せず同じ値
```

## Contract

- 1 回目の `get_or_init` で `f` を実行し値を保存する。2 回目以降は `f` を呼ばず **1 回目の値への参照（同じアドレス）** を返す。別のクロージャを渡しても無視される
- 複数スレッドから同時に呼んでも `f` はちょうど 1 回だけ実行され、他のスレッドは完了を待って同じ値を受け取る
- **`f` が panic すると未初期化のまま** で、panic はそのまま伝播する。次の `get_or_init` は `f` を **再実行** する
- `get()` は未初期化なら `None`。`set(v)` は 1 回目は `Ok(())`、2 回目以降は `Err(v)` で渡した値を返し、保存済みの値は変わらない
- `&mut` で所有していれば `take()` で値を取り出して未初期化に戻せ、`get_mut()` で書き換えられる。`static` ではどちらも使えない
- `f` は引数を取らない。引数ごとに 1 回にしたいなら function-memoize

## Alternatives

- 初期化クロージャを宣言時に固定できるなら `std::sync::LazyLock<T>`（Rust 1.80）。`*LAZY` で参照するだけで初回に初期化される
- 単一スレッドなら `std::cell::OnceCell<T>`（`Sync` ではないので `static` には置けない）
- 1.70 より前なら `once_cell` クレート（`once_cell::sync::OnceCell` / `Lazy`）。API はほぼ同じ
- 値を持たず副作用を 1 回にしたいだけなら `std::sync::Once::call_once`

## Pitfalls

- TypeScript（es-toolkit の `once`）は例外を投げた初期化も「実行済み」にして以後 `undefined` を返すが、`OnceLock` は Python の `functools.cache` と同じく **失敗した初期化を再試行する**
- 初期化クロージャの中から同じ `OnceLock` の `get_or_init` を呼ぶ（再入）と結果は未規定（ドキュメントでは現行実装はデッドロック）。自分自身を参照しない
- 返るのは `&T` で書き換えられない。実行時に変わる値は `OnceLock<Mutex<T>>` などにする
- `static` に置くには `T: Send + Sync` が必要。`Rc` や `RefCell` を含む型は置けない

## Test

`tests/function_once.rs`
