// collection-chunk: std::views::chunk の Contract を検証する
#include <algorithm>
#include <forward_list>
#include <ranges>
#include <span>
#include <sstream>
#include <string>
#include <vector>

#include "check.hpp"

namespace rv = std::views;
using Nested = std::vector<std::vector<int>>;

int main() {
  // 順序保持・最後が短い・切り捨てない
  std::vector<int> v{1, 2, 3, 4, 5};
  auto vv = v | rv::chunk(2) | std::ranges::to<Nested>();
  CHECK(vv == Nested({{1, 2}, {3, 4}, {5}}));
  CHECK(vv.back().size() == 1u);

  // sized / random_access: size() はチャンク数、添字でチャンクを取れる
  auto chunks = v | rv::chunk(2);
  static_assert(std::ranges::sized_range<decltype(chunks)>);
  static_assert(std::ranges::random_access_range<decltype(chunks)>);
  CHECK(std::ranges::size(chunks) == 3u);
  CHECK(std::ranges::equal(chunks[2], std::vector<int>{5}));

  // 遅延評価: ビュー作成後の変更が反映される
  v[0] = 100;
  CHECK((*chunks.begin())[0] == 100);

  // 各チャンクは元の要素を指すビュー。書き込むと元が変わる
  (*chunks.begin())[0] = 7;
  CHECK(v[0] == 7);
  CHECK(v == std::vector<int>({7, 2, 3, 4, 5}));

  // 何度でも走査できる
  int passes = 0;
  for (auto c : chunks) passes += static_cast<int>(std::ranges::size(c));
  for (auto c : chunks) passes += static_cast<int>(std::ranges::size(c));
  CHECK(passes == 10);

  // n が長さ以上なら全体が 1 チャンク
  auto big = v | rv::chunk(10);
  CHECK(std::ranges::size(big) == 1u);
  CHECK(std::ranges::size(*big.begin()) == 5u);

  // 空の範囲
  std::vector<int> empty;
  auto ce = empty | rv::chunk(2);
  CHECK(std::ranges::size(ce) == 0u);
  CHECK(ce.empty());

  // forward range（forward_list）でも使える
  std::forward_list<int> fl{1, 2, 3};
  CHECK(std::ranges::distance(fl | rv::chunk(2)) == 2);

  // input range（istream）: チャンクを順に 1 回だけ読める
  std::istringstream in("1 2 3 4 5");
  std::vector<int> sums;
  for (auto c : rv::istream<int>(in) | rv::chunk(2)) {
    int s = 0;
    for (int x : c) s += x;
    sums.push_back(s);
  }
  CHECK(sums == std::vector<int>({3, 7, 5}));

  // Alternatives: 短い末尾を捨てる / C++20 の span ループ
  std::vector<int> w{1, 2, 3, 4, 5};
  auto full = w | rv::chunk(2) | rv::take(w.size() / 2) | std::ranges::to<Nested>();
  CHECK(full == Nested({{1, 2}, {3, 4}}));
  Nested by_span;
  const std::size_t n = 2;
  for (std::size_t i = 0; i < w.size(); i += n) {
    auto c = std::span(w).subspan(i, std::min(n, w.size() - i));
    by_span.emplace_back(c.begin(), c.end());
  }
  CHECK(by_span == Nested({{1, 2}, {3, 4}, {5}}));

  // string は char 単位に切れる
  std::string s = "abcde";
  auto parts = s | rv::chunk(2) | std::ranges::to<std::vector<std::string>>();
  CHECK(parts == std::vector<std::string>({"ab", "cd", "e"}));

  FINISH();
}
