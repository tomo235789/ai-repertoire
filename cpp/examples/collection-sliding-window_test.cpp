// collection-sliding-window: std::views::slide の Contract を検証する
#include <algorithm>
#include <forward_list>
#include <functional>
#include <ranges>
#include <span>
#include <tuple>
#include <vector>

#include "check.hpp"

namespace rv = std::views;
using Nested = std::vector<std::vector<int>>;
using Pairs = std::vector<std::tuple<int, int>>;

int main() {
  // Usage: 幅 3 の窓を 1 つずつずらす。順序保持
  std::vector<int> v{1, 2, 3, 4, 5};
  auto win = v | rv::slide(3);
  CHECK((win | std::ranges::to<Nested>()) == Nested({{1, 2, 3}, {2, 3, 4}, {3, 4, 5}}));

  // sized / random_access: 窓の数は size - n + 1
  static_assert(std::ranges::sized_range<decltype(win)>);
  static_assert(std::ranges::random_access_range<decltype(win)>);
  CHECK(std::ranges::size(win) == 3u);
  CHECK(std::ranges::equal(win[2], std::vector<int>{3, 4, 5}));

  // n 未満なら空、等しければ 1 つ、n == 1 なら要素数
  CHECK(std::ranges::size(v | rv::slide(6)) == 0u);
  CHECK((v | rv::slide(6)).empty());
  CHECK(std::ranges::size(v | rv::slide(5)) == 1u);
  CHECK(std::ranges::size(v | rv::slide(1)) == 5u);
  std::vector<int> empty;
  CHECK(std::ranges::size(empty | rv::slide(2)) == 0u);

  // 遅延評価・窓は元への参照
  v[4] = 9;
  CHECK((*std::next(win.begin(), 2))[2] == 9);
  for (auto w : v | rv::slide(2)) w[0] += 10;
  CHECK(v == std::vector<int>({11, 12, 13, 14, 9}));

  // forward range でも走査できる
  std::forward_list<int> fl{1, 2, 3, 4};
  CHECK(std::ranges::distance(fl | rv::slide(3)) == 2);

  // step は stride で
  std::vector<int> u{1, 2, 3, 4, 5};
  CHECK((u | rv::slide(3) | rv::stride(2) | std::ranges::to<Nested>()) == Nested({{1, 2, 3}, {3, 4, 5}}));

  // Alternatives: adjacent<N> / pairwise / 移動平均 / C++20 の span ループ
  Pairs pairs;
  for (auto [a, b] : u | rv::adjacent<2>) pairs.emplace_back(a, b);
  CHECK(pairs == Pairs({{1, 2}, {2, 3}, {3, 4}, {4, 5}}));
  CHECK(std::ranges::distance(u | rv::pairwise) == 4);
  const int n = 3;
  auto ma = u | rv::slide(n) | rv::transform([n](auto w) { return std::ranges::fold_left(w, 0.0, std::plus{}) / n; });
  CHECK((ma | std::ranges::to<std::vector>()) == std::vector<double>({2.0, 3.0, 4.0}));
  Nested by_span;
  for (std::size_t i = 0; i + 3 <= u.size(); ++i) {
    auto w = std::span(u).subspan(i, 3);
    by_span.emplace_back(w.begin(), w.end());
  }
  CHECK(by_span == Nested({{1, 2, 3}, {2, 3, 4}, {3, 4, 5}}));

  // chunk との違い: chunk は重ならず末尾の短い塊も出る
  CHECK((u | rv::chunk(3) | std::ranges::to<Nested>()) == Nested({{1, 2, 3}, {4, 5}}));

  FINISH();
}
