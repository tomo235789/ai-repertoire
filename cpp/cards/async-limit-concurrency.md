---
id: async-limit-concurrency
lang: cpp
title: 非同期処理の同時実行数を制限する
tags: [同時実行数, 並列度, セマフォ, 流量制御, concurrency, semaphore, throttle, rate-limit]
lib: stdlib
fn: std::counting_semaphore
since: "C++20"
verified: 2026-09-17
status: public
---

同時に走らせる処理の数（同時に進行中のスレッド数・コネクション数）を初期カウンタの値までに抑える。コネクション数や並列度の上限に合わせて絞るのに使う。時間あたりの回数（API のレートリミット）を制限するものではなく、それには別にレートリミッタが要る。

## Signature

```cpp
template<std::ptrdiff_t LeastMaxValue> class std::counting_semaphore;  // acquire() / release(n = 1) / try_acquire() / try_acquire_for(d) / try_acquire_until(t)
```

## Usage

```cpp
#include <semaphore>
#include <thread>

std::counting_semaphore<2> sem(2);  // 同時に 2 つまで（テンプレート引数は上限の下限値を明示する）
auto worker = [&sem](int id) {
  sem.acquire();                   // 空きが出るまで待つ
  struct guard { std::counting_semaphore<2>& s; ~guard() { s.release(); } } g{sem};
  try { fetch(id); } catch (...) { /* 記録する。スレッド関数の外へ投げると std::terminate */ }
};
std::jthread t1(worker, 1), t2(worker, 2), t3(worker, 3);  // 同時に走るのは 2 つまで
```

## Contract

- `acquire()` は内部カウンタが正なら 1 減らして即座に戻り、0 なら他のスレッドの `release()` で正になるまでブロックする。初期値 2 なら 2 本のワーカーが同時に取得でき（`latch` で両方の取得を待ってから確認）、8 スレッドを走らせても同時に走る数は 2 を超えない
- `release(n = 1)` はカウンタを `n` 増やし、待っているスレッドを起こす。起こされる順序は規格上保証されない（FIFO ではない）
- `release()` は「対応する `acquire()` があったか」を検査しない。初期値を超えて増やせる（`counting_semaphore<3>(0)` に `release(3)` すると 3 回 `acquire` できる）。ただし `max()` を超える `release` は事前条件違反で **未定義動作**
- `try_acquire()` は待たずに試し、取れなければ `false`。規格上は空きがあっても `false` を返すことが許される
- `try_acquire_for(d)` / `try_acquire_until(t)` は制限時間まで待ち、取れなければ `false`（`20ms` を指定すると約 21ms 後に `false` が返った）
- `counting_semaphore<N>` の `N` はカウンタの最大値の下限で `max()` は `N` 以上。省略時は `PTRDIFF_MAX` だが、実際の上限は実装依存なので必要な値を明示する（同時 2 つなら `counting_semaphore<2>`）。`std::binary_semaphore` は `counting_semaphore<1>`
- コピーもムーブもできない。初期値は `0` 以上 `max()` 以下（負数は事前条件違反）

## Alternatives

- 同時に 1 つだけ（排他）なら `std::mutex` + `std::lock_guard`。`binary_semaphore` は所有者の概念が無く、別のスレッドが `release()` できる（通知用途）
- 全部終わるまで待つのは `std::latch` / `std::barrier`（C++20）
- `std::lock_guard` はセマフォには使えない（`lock()` / `unlock()` が無い）。Usage の `guard` のような RAII 型を書く
- 依存を増やせず単純でよければ `views::chunk`（collection-chunk）でタスクを分けてバッチごとに `jthread` を起動する

## Pitfalls

- `std::jthread` / `std::thread` のスレッド関数から例外が抜けると `std::terminate` が呼ばれ、スタック巻き戻し（guard の `release`）も保証されない。例外はスレッド関数の中で捕まえて記録する（`std::async` なら `future` に伝わる）

- `release()` を忘れると空きが戻らず、以後の `acquire()` は永久に待つ。`acquire()` の直後に RAII ラッパで包み、例外経路でも解放する
- 余分な `release()` の扱いが言語で違う。TypeScript（es-toolkit の `Semaphore`）は無視、Python の `BoundedSemaphore` は `ValueError`、C++ は黙ってカウンタが増え上限が崩れる。`max()` を超えると未定義動作
- 待機の順序は保証されない。順序が要るならキューを別に持つ
- 待機中の `acquire()` を外から取り消す手段は無い。制限時間が要るなら最初から `try_acquire_for` を使う
- `std::thread` を使うと `join()` 忘れで `std::terminate` する。`std::jthread` はデストラクタで `join()` する

## Test

`examples/async-limit-concurrency_test.cpp`
