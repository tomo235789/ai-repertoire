// collection-sort-by: std::ranges::stable_sort の Contract を検証する
#include <algorithm>
#include <cctype>
#include <optional>
#include <ranges>
#include <string>
#include <tuple>
#include <vector>

#include "check.hpp"

struct Row {
  std::string g;
  int v;
  int neg() const { return -v; }
  bool operator==(const Row&) const = default;
};
using Rows = std::vector<Row>;

int main() {
  // Usage: 複数キーは tie。in place
  Rows rows{{"b", 2}, {"a", 9}, {"b", 1}};
  auto ret = std::ranges::stable_sort(rows, {}, [](const Row& r) { return std::tie(r.g, r.v); });
  CHECK(rows == Rows({{"a", 9}, {"b", 1}, {"b", 2}}));
  CHECK(ret == rows.end());

  // 安定: 単一キーで同じキーの相対順を保つ。降順（greater）でも保つ
  Rows one{{"b", 2}, {"a", 9}, {"b", 1}, {"a", 3}};
  std::ranges::stable_sort(one, {}, &Row::g);
  CHECK(one == Rows({{"a", 9}, {"a", 3}, {"b", 2}, {"b", 1}}));
  Rows desc{{"b", 2}, {"a", 9}, {"b", 1}, {"a", 3}};
  std::ranges::stable_sort(desc, std::ranges::greater{}, &Row::g);
  CHECK(desc == Rows({{"b", 2}, {"b", 1}, {"a", 9}, {"a", 3}}));

  // 後ろのキーから順にかけると複数キーと同じ結果
  Rows twice{{"b", 2}, {"a", 9}, {"b", 1}, {"a", 3}};
  std::ranges::stable_sort(twice, {}, &Row::v);
  std::ranges::stable_sort(twice, {}, &Row::g);
  CHECK(twice == Rows({{"a", 3}, {"a", 9}, {"b", 1}, {"b", 2}}));

  // 副作用のあるプロジェクションでも結果の順序は同じ（呼び出し回数は実装依存なので検証しない）
  int calls = 0;
  std::vector<int> w{5, 4, 3, 2, 1, 0, 9, 8};
  std::ranges::stable_sort(w, {}, [&](int n) { ++calls; return n; });
  CHECK(w == std::vector<int>({0, 1, 2, 3, 4, 5, 8, 9}));

  // const メンバ関数をプロジェクションに渡せる
  Rows byneg{{"x", 1}, {"y", 3}, {"z", 2}};
  std::ranges::stable_sort(byneg, {}, &Row::neg);
  CHECK(byneg == Rows({{"y", 3}, {"z", 2}, {"x", 1}}));

  // 空の範囲
  std::vector<int> empty;
  std::ranges::stable_sort(empty);
  CHECK(empty.empty());

  // Alternatives: 非破壊はコピーしてから / min_element
  const Rows original{{"b", 2}, {"a", 9}};
  auto sorted = original;
  std::ranges::stable_sort(sorted, {}, &Row::g);
  CHECK(original == Rows({{"b", 2}, {"a", 9}}));
  CHECK(sorted == Rows({{"a", 9}, {"b", 2}}));
  CHECK(std::ranges::min_element(original, {}, &Row::v)->g == "b");

  // Pitfalls: optional は nullopt が先頭 / 文字列はバイト順で大文字が先
  std::vector<std::optional<int>> opts{3, std::nullopt, 1};
  std::ranges::stable_sort(opts);
  CHECK(opts == std::vector<std::optional<int>>({std::nullopt, 1, 3}));
  std::vector<std::string> s{"b", "A", "a", "B"};
  std::ranges::stable_sort(s);
  CHECK(s == std::vector<std::string>({"A", "B", "a", "b"}));
  std::vector<std::string> ci{"b", "A", "a", "B"};
  std::ranges::stable_sort(ci, {}, [](const std::string& x) {
    std::string lower = x;
    for (char& c : lower) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return lower;
  });
  CHECK(ci == std::vector<std::string>({"A", "a", "b", "B"}));

  FINISH();
}
