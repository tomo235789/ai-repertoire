// collection-take-while: std::views::take_while の Contract を検証する
#include <algorithm>
#include <ranges>
#include <stdexcept>
#include <string>
#include <vector>

#include "check.hpp"

namespace rv = std::views;

int main() {
  // Usage: 先頭から偽になるまで。順序保持
  std::vector<int> v{1, 2, 3, 4, 1};
  auto head = v | rv::take_while([](int n) { return n < 3; });
  CHECK((head | std::ranges::to<std::vector>()) == std::vector<int>({1, 2}));
  static_assert(std::ranges::random_access_range<decltype(head)>);
  static_assert(!std::ranges::sized_range<decltype(head)>);
  CHECK(std::ranges::distance(head) == 2);

  // 述語は走査のたびに評価される。1 回の for では偽になった要素まで
  int calls = 0;
  auto counted = v | rv::take_while([&](int n) { ++calls; return n < 3; });
  for (int x : counted) (void)x;
  CHECK(calls == 3);  // 1, 2, 3 で評価し 3 で止まる
  for (int x : counted) (void)x;
  CHECK(calls == 6);
  auto out = counted | std::ranges::to<std::vector>();  // ranges::to の走査回数は実装依存なので数えない
  CHECK(out == std::vector<int>({1, 2}));

  // 遅延評価・要素は元への参照
  v[1] = 100;
  CHECK(std::ranges::distance(head) == 1);
  v[1] = 2;
  for (int& x : head) x *= 10;
  CHECK(v == std::vector<int>({10, 20, 3, 4, 1}));

  // すべて真 / 先頭で偽 / 空
  CHECK(std::ranges::distance(v | rv::take_while([](int) { return true; })) == 5);
  auto none = v | rv::take_while([](int) { return false; });
  CHECK(none.begin() == none.end());
  std::vector<int> empty;
  auto te = empty | rv::take_while([](int) { return true; });
  CHECK(te.begin() == te.end());

  // 述語の例外は伝播する
  auto bad = v | rv::take_while([](int) -> bool { throw std::runtime_error("boom"); });
  CHECK_THROWS((void)(bad.begin() == bad.end()), std::runtime_error);

  // Alternatives: drop_while とつなぐと元に戻る / filter との違い / find_if_not
  std::vector<int> w{1, 2, 3, 4, 1};
  auto lt3 = [](int n) { return n < 3; };
  auto tail = w | rv::drop_while(lt3) | std::ranges::to<std::vector>();
  CHECK(tail == std::vector<int>({3, 4, 1}));
  auto joined = w | rv::take_while(lt3) | std::ranges::to<std::vector>();
  joined.insert(joined.end(), tail.begin(), tail.end());
  CHECK(joined == w);
  CHECK((w | rv::filter(lt3) | std::ranges::to<std::vector>()) == std::vector<int>({1, 2, 1}));
  auto it = std::ranges::find_if_not(w, lt3);
  CHECK(std::ranges::equal(std::ranges::subrange(w.begin(), it), std::vector<int>{1, 2}));

  // 文字列の先頭の数字部分
  std::string s = "123abc";
  auto digits = s | rv::take_while([](char c) { return c >= '0' && c <= '9'; }) | std::ranges::to<std::string>();
  CHECK(digits == "123");

  FINISH();
}
