// collection-partition: std::ranges::stable_partition の Contract を検証する
#include <algorithm>
#include <functional>
#include <iterator>
#include <list>
#include <ranges>
#include <stdexcept>
#include <string>
#include <vector>

#include "check.hpp"

struct Item {
  std::string name;
  bool active;
  bool operator==(const Item&) const = default;
};

int main() {
  // Usage: in place で真が前、偽が後ろ。返り値は偽側
  std::vector<int> v{1, 2, 3, 4, 5, 6};
  auto odd = std::ranges::stable_partition(v, [](int n) { return n % 2 == 0; });
  auto even = std::ranges::subrange(v.begin(), odd.begin());
  CHECK(v == std::vector<int>({2, 4, 6, 1, 3, 5}));
  CHECK(std::ranges::equal(even, std::vector<int>{2, 4, 6}));
  CHECK(std::ranges::equal(odd, std::vector<int>{1, 3, 5}));
  CHECK(odd.begin() - v.begin() == 3);
  CHECK(odd.end() == v.end());
  CHECK(std::ranges::size(odd) == 3u);

  // 述語は各要素につきちょうど 1 回
  int calls = 0;
  std::vector<int> w{1, 2, 3, 4, 5};
  std::ranges::stable_partition(w, [&](int n) { ++calls; return n > 2; });
  CHECK(calls == 5);
  CHECK(w == std::vector<int>({3, 4, 5, 1, 2}));

  // プロジェクション
  std::vector<Item> items{{"a", false}, {"b", true}, {"c", false}, {"d", true}};
  auto inactive = std::ranges::stable_partition(items, std::identity{}, &Item::active);
  CHECK(items == std::vector<Item>({{"b", true}, {"d", true}, {"a", false}, {"c", false}}));
  CHECK(std::ranges::size(inactive) == 2u);

  // すべて真 / すべて偽 / 空
  std::vector<int> all{2, 4};
  CHECK(std::ranges::stable_partition(all, [](int n) { return n % 2 == 0; }).empty());
  std::vector<int> none{1, 3};
  CHECK(std::ranges::size(std::ranges::stable_partition(none, [](int n) { return n % 2 == 0; })) == 2u);
  std::vector<int> empty;
  CHECK(std::ranges::stable_partition(empty, [](int) { return true; }).empty());

  // list（bidirectional）でも使える。size() は無いので distance
  std::list<int> l{1, 2, 3, 4, 5};
  auto lt = std::ranges::stable_partition(l, [](int n) { return n % 2 == 0; });
  CHECK(l == std::list<int>({2, 4, 1, 3, 5}));
  CHECK(std::ranges::distance(lt) == 3);

  // 述語の例外は伝播する
  std::vector<int> t{1, 2};
  CHECK_THROWS(std::ranges::stable_partition(t, [](int) -> bool { throw std::runtime_error("boom"); }),
               std::runtime_error);

  // Alternatives: partition_copy は入力を変えない（真側が先の引数）
  std::vector<int> src{1, 2, 3, 4, 5}, evens, odds;
  std::ranges::partition_copy(src, std::back_inserter(evens), std::back_inserter(odds),
                              [](int n) { return n % 2 == 0; });
  CHECK(evens == std::vector<int>({2, 4}));
  CHECK(odds == std::vector<int>({1, 3, 5}));
  CHECK(src == std::vector<int>({1, 2, 3, 4, 5}));

  // Alternatives: filter と not_fn は遅延で 2 回走査
  auto f_even = src | std::views::filter([](int n) { return n % 2 == 0; });
  auto f_odd = src | std::views::filter(std::not_fn([](int n) { return n % 2 == 0; }));
  CHECK(std::ranges::equal(f_even, evens));
  CHECK(std::ranges::equal(f_odd, odds));

  // Alternatives: partition_point は分割済み範囲の境界
  CHECK(std::ranges::partition_point(v, [](int n) { return n % 2 == 0; }) == odd.begin());

  FINISH();
}
