// collection-group-by: std::views::chunk_by の Contract を検証する
#include <algorithm>
#include <map>
#include <ranges>
#include <stdexcept>
#include <string>
#include <vector>

#include "check.hpp"

namespace rv = std::views;
using Groups = std::vector<std::vector<std::string>>;

int main() {
  // Usage: キーで整列してから隣接をまとめる
  std::vector<std::string> words{"bob", "apple", "cat", "dove"};
  std::ranges::stable_sort(words, {}, &std::string::size);
  auto groups = words | rv::chunk_by([](auto& a, auto& b) { return a.size() == b.size(); });
  CHECK((groups | std::ranges::to<Groups>()) == Groups({{"bob", "cat"}, {"dove"}, {"apple"}}));

  // 隣接する要素しかまとめない（離れた同じキーは別グループ）
  std::vector<int> v{1, 1, 2, 2, 1, 3, 3};
  auto adj = v | rv::chunk_by(std::ranges::equal_to{}) | std::ranges::to<std::vector<std::vector<int>>>();
  CHECK(adj == std::vector<std::vector<int>>({{1, 1}, {2, 2}, {1}, {3, 3}}));

  // sized ではない / bidirectional まで / distance でグループ数
  auto gv = v | rv::chunk_by(std::ranges::equal_to{});
  static_assert(!std::ranges::sized_range<decltype(gv)>);
  static_assert(std::ranges::bidirectional_range<decltype(gv)>);
  static_assert(!std::ranges::random_access_range<decltype(gv)>);
  CHECK(std::ranges::distance(gv) == 4);

  // 遅延評価: 作成後の変更が反映され、グループ経由の書き込みが元に届く
  std::vector<int> w{1, 1, 2};
  auto gw = w | rv::chunk_by(std::ranges::equal_to{});
  w[1] = 5;
  CHECK(std::ranges::distance(*gw.begin()) == 1);
  (*gw.begin())[0] = 9;
  CHECK(w == std::vector<int>({9, 5, 2}));

  // 述語は走査のたびに隣接ペアごとに呼ばれる。begin() の分だけキャッシュされる
  int calls = 0;
  std::vector<int> u{1, 1, 2, 3, 3};
  auto gu = u | rv::chunk_by([&](int a, int b) { ++calls; return a == b; });
  for (auto g : gu) (void)g;
  CHECK(calls == 4);  // 隣接ペアは 4 組
  for (auto g : gu) (void)g;
  CHECK(calls == 6);  // 最初の境界（2 回分）はキャッシュ済み

  // 空の範囲
  std::vector<int> empty;
  auto ge = empty | rv::chunk_by(std::ranges::equal_to{});
  CHECK(ge.begin() == ge.end());
  CHECK(std::ranges::distance(ge) == 0);

  // 述語の例外は伝播する
  auto gt = u | rv::chunk_by([](int, int) -> bool { throw std::runtime_error("boom"); });
  CHECK_THROWS((void)gt.begin(), std::runtime_error);

  // Alternatives: map への集約は隣接に依存しない
  std::vector<std::string> ws{"apple", "banana", "avocado", "cherry"};
  std::map<char, std::vector<std::string>> m;
  for (auto& s : ws) m[s[0]].push_back(s);
  CHECK(m.size() == 3u);
  CHECK(m['a'] == std::vector<std::string>({"apple", "avocado"}));

  // Alternatives: less で昇順に続く区間を切り出す
  std::vector<int> runs{1, 2, 3, 1, 2};
  auto up = runs | rv::chunk_by(std::ranges::less{}) | std::ranges::to<std::vector<std::vector<int>>>();
  CHECK(up == std::vector<std::vector<int>>({{1, 2, 3}, {1, 2}}));

  FINISH();
}
