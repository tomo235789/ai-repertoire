// number-clamp: std::clamp の Contract を検証する
#include <algorithm>
#include <cmath>
#include <functional>
#include <string>

#include "check.hpp"

struct Item {
  std::string name;
  int score;
};

int main() {
  // 境界値を含む
  CHECK(std::clamp(120, 0, 100) == 100);
  CHECK(std::clamp(-5, 0, 100) == 0);
  CHECK(std::clamp(42, 0, 100) == 42);
  CHECK(std::clamp(0, 0, 100) == 0);
  CHECK(std::clamp(100, 0, 100) == 100);
  CHECK(std::clamp(5.0, 0.0, 1.0) == 1.0);
  CHECK(std::clamp(5'000'000'000LL, 0LL, 100LL) == 100LL);

  // 返り値は引数への参照。範囲内なら v そのもの、範囲外なら境界の参照
  int x = 5, lo = 0, hi = 10;
  const int& r = std::clamp(x, lo, hi);
  CHECK(&r == &x);
  int big = 99;
  const int& rh = std::clamp(big, lo, hi);
  CHECK(&rh == &hi);
  int copied = std::clamp(120, 0, 100);  // 値で受ければ一時オブジェクトでも安全
  CHECK(copied == 100);

  // 引数を変更しない
  CHECK(x == 5 && lo == 0 && hi == 10);

  // 型を明示すれば int と double を混ぜられる
  CHECK(std::clamp<double>(5, 0.0, 10.0) == 5.0);

  // NaN は std::clamp の比較要件を満たさず未サポート。呼び出し前に std::isnan で弾く方針を検証する
  const double nan = std::nan("");
  auto clamp_or_nan = [](double v, double lo, double hi) -> double {
    if (std::isnan(v) || std::isnan(lo) || std::isnan(hi)) return std::nan("");
    return std::clamp(v, lo, hi);
  };
  CHECK(std::isnan(clamp_or_nan(nan, 0.0, 1.0)));
  CHECK(std::isnan(clamp_or_nan(5.0, nan, 1.0)));
  CHECK(std::isnan(clamp_or_nan(5.0, 0.0, nan)));
  CHECK(clamp_or_nan(5.0, 0.0, 1.0) == 1.0);

  // 比較関数を渡す（greater なら lo >= hi の順）
  CHECK(std::clamp(5, 10, 0, std::greater<int>{}) == 5);
  CHECK(std::clamp(20, 10, 0, std::greater<int>{}) == 10);
  CHECK(std::clamp(-1, 10, 0, std::greater<int>{}) == 0);

  // constexpr
  static_assert(std::clamp(120, 0, 100) == 100);

  // ranges::clamp は射影でメンバ比較できる
  const Item it{"a", 250};
  const Item lo_item{"lo", 0}, hi_item{"hi", 100};
  const Item& c = std::ranges::clamp(it, lo_item, hi_item, {}, &Item::score);
  CHECK(c.name == "hi" && c.score == 100);
  CHECK(&std::ranges::clamp(it, lo_item, Item{"hi", 300}, {}, &Item::score) == &it);

  FINISH();
}
