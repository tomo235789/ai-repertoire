// async-limit-concurrency: std::counting_semaphore の Contract を検証する
#include <atomic>
#include <chrono>
#include <cstddef>
#include <latch>
#include <semaphore>
#include <thread>
#include <type_traits>
#include <vector>

#include "check.hpp"

using namespace std::chrono_literals;

// acquire 済みのセマフォをスコープ終了で release する RAII ラッパ（上限値の異なる特殊化を受ける）
template <std::ptrdiff_t N>
struct guard {
  std::counting_semaphore<N>& s;
  ~guard() { s.release(); }
};

int main() {
  // 初期値 2 なら 2 本のワーカーが同時に取得できる。latch で両方の取得を待ってから確かめる
  std::counting_semaphore<2> sem(2);
  {
    std::latch both_acquired(2), release_now(1);
    std::atomic<int> holding{0};
    auto hold = [&] {
      sem.acquire();
      guard<2> g{sem};
      ++holding;
      both_acquired.count_down();
      release_now.wait();
    };
    std::jthread a(hold), b(hold);
    both_acquired.wait();
    CHECK(holding == 2);
    CHECK(!sem.try_acquire());  // 2 つとも取得中なので 3 つ目は取れない
    release_now.count_down();
  }
  sem.acquire();  // 両方 release 済みなので取得できる（try_acquire は空きがあっても false を返せるので使わない）
  sem.release();

  // 8 スレッドを走らせても同時実行数は 2 を超えず、全タスクが完了する
  std::atomic<int> running{0}, peak{0}, done{0};
  {
    std::vector<std::jthread> workers;
    for (int i = 0; i < 8; ++i) {
      workers.emplace_back([&] {
        sem.acquire();
        guard<2> g{sem};
        const int now = ++running;
        int seen = peak.load();
        while (now > seen && !peak.compare_exchange_weak(seen, now)) {
        }
        std::this_thread::sleep_for(20ms);
        --running;
        ++done;
      });
    }
  }
  CHECK(peak <= 2);
  CHECK(done == 8);
  sem.acquire();  // 全員 release 済みなので空きがある
  sem.release();

  // try_acquire は空きが無ければ待たずに false（空きがあるときの成功は規格が保証しないので検証しない）
  std::counting_semaphore<1> one(1);
  one.acquire();
  CHECK(!one.try_acquire());
  one.release();
  one.acquire();

  // try_acquire_for / until は制限時間で諦める
  const auto t0 = std::chrono::steady_clock::now();
  CHECK(!one.try_acquire_for(20ms));
  const auto elapsed = std::chrono::steady_clock::now() - t0;
  CHECK(elapsed >= 20ms);
  CHECK(!one.try_acquire_until(std::chrono::steady_clock::now() + 5ms));

  // release(n) と初期値を超える release（上限 3 の特殊化に 0 から 3 回分）
  std::counting_semaphore<3> zero(0);
  CHECK(!zero.try_acquire());
  zero.release(3);
  for (int i = 0; i < 3; ++i) zero.acquire();  // 3 回分は待たずに取れる
  CHECK(!zero.try_acquire());                   // 4 回目は無い

  // release で待機中のスレッドが起きる
  std::counting_semaphore<1> gate(0);
  std::atomic<bool> woke{false};
  std::jthread waiter([&] {
    gate.acquire();
    woke = true;
  });
  std::this_thread::sleep_for(10ms);
  CHECK(!woke);
  gate.release();
  waiter.join();
  CHECK(woke);

  // max() は N 以上。binary_semaphore は counting_semaphore<1>
  CHECK(std::counting_semaphore<5>::max() >= 5);
  CHECK(std::counting_semaphore<2>::max() >= 2);
  static_assert(std::is_same_v<std::binary_semaphore, std::counting_semaphore<1>>);
  std::binary_semaphore b(0);
  CHECK(!b.try_acquire());
  b.release();
  b.acquire();

  // コピー・ムーブ不可
  static_assert(!std::is_copy_constructible_v<std::counting_semaphore<2>>);
  static_assert(!std::is_move_constructible_v<std::counting_semaphore<2>>);

  // RAII ラッパは例外経路でも release する
  std::counting_semaphore<1> s(1);
  try {
    s.acquire();
    guard<1> g{s};
    throw 1;
  } catch (int) {
  }
  s.acquire();  // guard が release 済みなので取得できる

  FINISH();
}
