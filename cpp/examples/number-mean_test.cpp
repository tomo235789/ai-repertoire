// number-mean: std::ranges::fold_left による平均の Contract を検証する
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <numeric>
#include <ranges>
#include <sstream>
#include <type_traits>
#include <utility>
#include <vector>

#include "check.hpp"

double mean(const std::vector<double>& v) { return std::ranges::fold_left(v, 0.0, std::plus{}) / v.size(); }

int main() {
  namespace rv = std::views;

  // 初期値 0.0 で double。整数の平均も切り捨てない
  const std::vector<int> v{1, 2, 3, 4};
  auto m = std::ranges::fold_left(v, 0.0, std::plus{}) / v.size();
  static_assert(std::is_same_v<decltype(m), double>);
  CHECK(m == 2.5);
  const std::vector<int> two{1, 2};
  CHECK(std::ranges::fold_left(two, 0.0, std::plus{}) / two.size() == 1.5);
  CHECK(std::ranges::fold_left(two, 0, std::plus{}) / static_cast<int>(two.size()) == 1);  // 整数除算

  // 空は NaN（double の 0 除算）。例外は投げない
  static_assert(std::numeric_limits<double>::is_iec559);
  CHECK(std::isnan(mean({})));

  // 入力を変更しない
  CHECK(v == std::vector<int>({1, 2, 3, 4}));

  // 素朴な加算。NaN / inf
  CHECK(mean({0.1, 0.2, 0.3}) == 0.20000000000000004);
  CHECK(std::isnan(mean({1.0, std::nan("")})));
  const double inf = std::numeric_limits<double>::infinity();
  CHECK(std::isnan(mean({inf, -inf})));
  CHECK(mean({inf, 1.0}) == inf);

  // size() の無いビューは ranges::distance で数える
  auto evens = v | rv::filter([](int x) { return x % 2 == 0; });
  CHECK(std::ranges::fold_left(evens, 0.0, std::plus{}) / std::ranges::distance(evens) == 3.0);

  // 単一パスの input range は合計で消費され distance が 0 になる。合計と個数を同じ走査で集計する
  std::istringstream consumed("1 2 3 4 5 6");
  auto once = rv::istream<int>(consumed) | rv::filter([](int x) { return x % 2 == 0; });
  static_assert(!std::ranges::forward_range<decltype(once)>);
  CHECK(std::ranges::fold_left(once, 0.0, std::plus{}) == 12.0);
  CHECK(std::ranges::distance(once) == 0);
  std::istringstream in("1 2 3 4 5 6");
  auto stream = rv::istream<int>(in) | rv::filter([](int x) { return x % 2 == 0; });
  auto [sum1, count1] = std::ranges::fold_left(stream, std::pair{0.0, 0}, [](auto acc, int x) {
    return std::pair{acc.first + x, acc.second + 1};
  });
  CHECK(count1 == 3 && sum1 / count1 == 4.0);

  // Alternatives
  CHECK(std::midpoint(1, 2) == 1);
  CHECK(std::midpoint(1.0, 2.0) == 1.5);
  CHECK(std::midpoint(2147483647, 2147483645) == 2147483646);
  struct Item { int score; };
  const std::vector<Item> items{{10}, {20}, {60}};
  CHECK(std::ranges::fold_left(items | rv::transform(&Item::score), 0.0, std::plus{}) / items.size() == 30.0);
  CHECK(std::accumulate(v.begin(), v.end(), 0.0) / v.size() == 2.5);

  // Pitfalls: int 合計を size_t で割ると符号なしに変換される
  const std::vector<int> neg{-1, -3};
  const int sum = std::ranges::fold_left(neg, 0, std::plus{});
  CHECK(sum / neg.size() > 1'000'000'000u);
  CHECK(static_cast<double>(sum) / neg.size() == -2.0);

  FINISH();
}
