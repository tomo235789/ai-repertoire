// function-once: std::call_once の Contract を検証する
#include <atomic>
#include <chrono>
#include <cstdio>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <vector>

#include "check.hpp"

int main() {
  // 最初の 1 回だけ実行。別の関数を渡しても実行されない
  std::once_flag flag;
  int calls = 0, which = 0;
  for (int i = 0; i < 3; ++i) std::call_once(flag, [&] { ++calls; which = 1; });
  std::call_once(flag, [&] { ++calls; which = 2; });
  CHECK(calls == 1);
  CHECK(which == 1);
  static_assert(std::is_void_v<decltype(std::call_once(flag, [] {}))>);

  // 引数は転送される。2 回目の引数は無視
  std::once_flag with_args;
  int got = 0;
  std::call_once(with_args, [&](int a, int b) { got = a + b; }, 1, 2);
  std::call_once(with_args, [&](int a, int b) { got = a * b * 100; }, 1, 2);
  CHECK(got == 3);

  // 複数スレッドからでも 1 回。他のスレッドは完了を待ち、副作用が見える
  std::once_flag shared;
  std::atomic<int> runs{0}, saw_value{0};
  int value = 0;
  {
    std::vector<std::jthread> threads;
    for (int i = 0; i < 8; ++i) {
      threads.emplace_back([&] {
        std::call_once(shared, [&] {
          std::this_thread::sleep_for(std::chrono::milliseconds(20));
          value = 42;
          ++runs;
        });
        if (value == 42) ++saw_value;
      });
    }
  }
  CHECK(runs == 1);
  CHECK(saw_value == 8);

  // 例外を投げると未実行扱いで次の呼び出しが再実行する
#if !defined(__GLIBCXX__) || defined(_GLIBCXX_HAVE_LINUX_FUTEX)
  std::once_flag retry;
  int attempts = 0;
  auto init = [&] {
    std::call_once(retry, [&] {
      ++attempts;
      if (attempts < 2) throw std::runtime_error("fail");
    });
  };
  CHECK_THROWS(init(), std::runtime_error);
  init();
  init();
  CHECK(attempts == 2);
#else
  // macOS など futex の無い libstdc++ では例外後の call_once がデッドロックするため検証しない
  std::printf("skip: call_once の例外後の再実行はこのプラットフォームの libstdc++ では固まるため検証しない\n");
#endif

  // once_flag はコピー・ムーブ不可
  static_assert(!std::is_copy_constructible_v<std::once_flag>);
  static_assert(!std::is_move_constructible_v<std::once_flag>);

  // Alternatives: マジックスタティックは例外で再試行し、値を返す
  int tries = 0;
  auto magic = [&]() -> int {
    static const int v = [&] {
      ++tries;
      if (tries < 2) throw std::runtime_error("fail");
      return 7;
    }();
    return v;
  };
  CHECK_THROWS(magic(), std::runtime_error);
  CHECK(magic() == 7);
  CHECK(magic() == 7);
  CHECK(tries == 2);

  FINISH();
}
