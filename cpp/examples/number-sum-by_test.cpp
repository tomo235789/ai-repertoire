// number-sum-by: std::ranges::fold_left による合計の Contract を検証する
#include <algorithm>
#include <cmath>
#include <functional>
#include <list>
#include <numeric>
#include <optional>
#include <ranges>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

#include "check.hpp"

struct Item {
  std::string name;
  int qty;
  double price;
};

int main() {
  namespace rv = std::views;
  const std::vector<Item> items{{"a", 2, 1.5}, {"b", 3, 2.25}};

  // 基本: メンバを取り出して合計
  CHECK(std::ranges::fold_left(items | rv::transform(&Item::qty), 0, std::plus{}) == 5);
  CHECK(std::ranges::fold_left(items, 0, [](int acc, const Item& it) { return acc + it.qty; }) == 5);
  CHECK(items[0].qty == 2 && items[1].qty == 3);  // 入力は変わらない

  // 取り出し関数は各要素につき 1 回、先頭から順に呼ばれる
  std::vector<std::string> seen;
  std::ranges::fold_left(items | rv::transform([&](const Item& it) { seen.push_back(it.name); return it.qty; }), 0, std::plus{});
  CHECK(seen == std::vector<std::string>({"a", "b"}));

  // 空なら init
  const std::vector<Item> empty;
  CHECK(std::ranges::fold_left(empty | rv::transform(&Item::qty), 0, std::plus{}) == 0);

  // 返り値の型は f(init, 要素) の型。int 初期値 + double 要素は double で切り捨てない
  auto total = std::ranges::fold_left(items | rv::transform(&Item::price), 0, std::plus{});
  static_assert(std::is_same_v<decltype(total), double>);
  CHECK(total == 3.75);
  auto wide = std::ranges::fold_left(items | rv::transform(&Item::qty), 0LL, std::plus{});
  static_assert(std::is_same_v<decltype(wide), long long>);
  CHECK(wide == 5LL);
  const std::vector<unsigned char> uc{200, 100};
  auto promoted = std::ranges::fold_left(uc, static_cast<unsigned char>(0), std::plus{});
  static_assert(std::is_same_v<decltype(promoted), int>);
  CHECK(promoted == 300);

  // double は素朴な加算。NaN は伝播
  const std::vector<double> d{0.1, 0.2, 0.3};
  CHECK(std::ranges::fold_left(d, 0.0, std::plus{}) == 0.60000000000000009);
  const std::vector<double> with_nan{1.0, std::nan("")};
  CHECK(std::isnan(std::ranges::fold_left(with_nan, 0.0, std::plus{})));

  // 例外は伝播する
  CHECK_THROWS(std::ranges::fold_left(items | rv::transform([](const Item&) -> int { throw std::runtime_error("x"); }), 0, std::plus{}),
               std::runtime_error);

  // input_range なら何でもよい
  const std::list<int> l{1, 2, 3};
  CHECK(std::ranges::fold_left(l, 0, std::plus{}) == 6);

  // Alternatives: accumulate は初期値の型で切り捨てる。fold_left_first は空で nullopt
  const std::vector<double> prices{1.5, 2.25};
  auto acc = std::accumulate(prices.begin(), prices.end(), 0);
  static_assert(std::is_same_v<decltype(acc), int>);
  CHECK(acc == 3);
  CHECK(std::accumulate(prices.begin(), prices.end(), 0.0) == 3.75);
  CHECK(std::ranges::fold_left_first(l, std::plus{}) == std::optional<int>{6});
  CHECK(!std::ranges::fold_left_first(std::vector<int>{}, std::plus{}).has_value());

  FINISH();
}
