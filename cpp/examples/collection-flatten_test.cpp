// collection-flatten: std::views::join の Contract を検証する
#include <algorithm>
#include <list>
#include <ranges>
#include <string>
#include <string_view>
#include <vector>

#include "check.hpp"

namespace rv = std::views;

int main() {
  // Usage: 1 段だけ開く。順序保持
  std::vector<std::vector<int>> nested{{1, 2}, {}, {3}, {4, 5}};
  auto flat = nested | rv::join;
  CHECK((flat | std::ranges::to<std::vector>()) == std::vector<int>({1, 2, 3, 4, 5}));
  static_assert(std::ranges::bidirectional_range<decltype(flat)>);
  static_assert(!std::ranges::sized_range<decltype(flat)>);
  CHECK(std::ranges::distance(flat) == 5);

  // 2 段の入れ子は 1 段しか開かない。2 回つなぐと全部開く
  std::vector<std::vector<std::vector<int>>> deep{{{1}, {2}}, {{3}}};
  auto once = deep | rv::join;
  CHECK(std::ranges::distance(once) == 3);
  CHECK((*once.begin()) == std::vector<int>{1});
  CHECK((deep | rv::join | rv::join | std::ranges::to<std::vector>()) == std::vector<int>({1, 2, 3}));

  // 遅延評価・要素は元への参照
  nested[1].push_back(9);  // 外側の vector は再確保されないので flat はそのまま使える
  CHECK((flat | std::ranges::to<std::vector>()) == std::vector<int>({1, 2, 9, 3, 4, 5}));
  for (int& x : nested | rv::join) x *= 10;
  CHECK(nested[0] == std::vector<int>({10, 20}));
  CHECK(nested[3] == std::vector<int>({40, 50}));

  // transform が値で返す内側の範囲: input range になる
  std::vector<int> src{1, 2, 3};
  auto gen = src | rv::transform([](int n) { return std::vector<int>(n, n); }) | rv::join;
  static_assert(std::ranges::input_range<decltype(gen)>);
  static_assert(!std::ranges::forward_range<decltype(gen)>);
  CHECK((gen | std::ranges::to<std::vector>()) == std::vector<int>({1, 2, 2, 3, 3, 3}));

  // 内側の型は list でもよい
  std::vector<std::list<int>> vl{{1, 2}, {3}};
  CHECK((vl | rv::join | std::ranges::to<std::vector>()) == std::vector<int>({1, 2, 3}));

  // 空の外側 / 空の内側だけ
  std::vector<std::vector<int>> empty;
  auto je = empty | rv::join;
  CHECK(je.begin() == je.end());
  std::vector<std::vector<int>> empties{{}, {}};
  auto jee = empties | rv::join;
  CHECK(jee.begin() == jee.end());

  // vector<string> は char の範囲になる
  std::vector<std::string> words{"ab", "cd"};
  CHECK((words | rv::join | std::ranges::to<std::string>()) == "abcd");

  // Alternatives: join_with / transform + join / C++20 の for ループ
  CHECK((words | rv::join_with(std::string_view(", ")) | std::ranges::to<std::string>()) == "ab, cd");
  CHECK((words | rv::join_with('-') | std::ranges::to<std::string>()) == "ab-cd");
  // 文字列リテラルを直接呼び出しに渡すと配列として受理され、末尾の NUL も区切りに含まれる
  const std::string with_nul = rv::join_with(words, ", ") | std::ranges::to<std::string>();
  CHECK(with_nul.size() == 7 && with_nul[4] == '\0');
  CHECK(with_nul == std::string("ab, \0cd", 7));
  std::vector<int> out;
  for (int x : nested | rv::join) out.push_back(x);
  CHECK(out == std::vector<int>({10, 20, 90, 30, 40, 50}));

  FINISH();
}
