// collection-zip: std::views::zip の Contract を検証する
#include <algorithm>
#include <array>
#include <functional>
#include <ranges>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

#include "check.hpp"

namespace rv = std::views;
using Triple = std::tuple<int, std::string, double>;
using IdName = std::vector<std::pair<int, std::string>>;
using Indexed = std::vector<std::pair<long, std::string>>;

int main() {
  // 最短に合わせて打ち切る。要素は tuple
  std::vector<int> ids{1, 2, 3};
  std::vector<std::string> names{"a", "b"};
  std::array<double, 3> scores{1.5, 2.5, 3.5};
  auto z = rv::zip(ids, names, scores);
  static_assert(std::ranges::sized_range<decltype(z)>);
  static_assert(std::ranges::random_access_range<decltype(z)>);
  CHECK(std::ranges::size(z) == 2u);
  std::vector<Triple> seen;
  for (auto [id, name, score] : z) seen.emplace_back(id, name, score);
  CHECK(seen == std::vector<Triple>({{1, "a", 1.5}, {2, "b", 2.5}}));
  CHECK(std::get<1>(z[1]) == "b");

  // 要素は参照の tuple。const な範囲は const T&
  static_assert(std::is_same_v<decltype(*z.begin()), std::tuple<int&, std::string&, double&>>);
  const std::vector<int> cids{1, 2};
  static_assert(std::is_same_v<decltype(*rv::zip(cids, names).begin()), std::tuple<const int&, std::string&>>);

  // auto [a, b]（&& 無し）で受けても書き込みは元に届く
  for (auto [id, name] : rv::zip(ids, names)) {
    id *= 10;
    name += "!";
  }
  CHECK(ids == std::vector<int>({10, 20, 3}));
  CHECK(names == std::vector<std::string>({"a!", "b!"}));

  // 遅延評価
  std::vector<int> la{1, 2};
  auto zl = rv::zip(la, names);
  la[0] = 9;
  CHECK(std::get<0>(*zl.begin()) == 9);

  // いずれかが空なら空。引数なしは tuple<> の空ビュー
  std::vector<int> empty;
  CHECK(std::ranges::size(rv::zip(ids, empty)) == 0u);
  CHECK(std::ranges::size(rv::zip()) == 0u);

  // sized でない範囲と組んでも最短で止まる
  auto tw = ids | rv::take_while([](int n) { return n < 15; });
  CHECK(std::ranges::distance(rv::zip(ids, tw)) == 1);

  // zip した範囲を sort すると両方が同時に並べ替わる
  std::vector<int> keys{3, 1, 2};
  std::vector<std::string> vals{"c", "a", "b"};
  std::ranges::sort(rv::zip(keys, vals));
  CHECK(keys == std::vector<int>({1, 2, 3}));
  CHECK(vals == std::vector<std::string>({"a", "b", "c"}));

  // 右辺値を渡すとビューが所有する
  auto owned = rv::zip(std::vector<int>{1, 2}, std::vector<int>{3, 4, 5});
  CHECK(std::ranges::size(owned) == 2u);

  // Alternatives: pair への実体化 / enumerate / zip_transform
  auto pairs = rv::zip(keys, vals) | std::ranges::to<IdName>();
  CHECK(pairs == IdName({{1, "a"}, {2, "b"}, {3, "c"}}));
  Indexed en;
  for (auto [i, s] : rv::enumerate(vals)) en.emplace_back(i, s);
  CHECK(en == Indexed({{0, "a"}, {1, "b"}, {2, "c"}}));
  auto sums = rv::zip_transform(std::plus{}, keys, std::vector<int>{10, 20, 30}) | std::ranges::to<std::vector>();
  CHECK(sums == std::vector<int>({11, 22, 33}));

  FINISH();
}
