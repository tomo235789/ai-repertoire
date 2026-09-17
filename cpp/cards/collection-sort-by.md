---
id: collection-sort-by
lang: cpp
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, 複数キー, sort, stable-sort, projection]
lib: stdlib
fn: std::ranges::stable_sort
since: "C++20"
verified: 2026-09-17
preserves_order: true
status: public
---

プロジェクション（キー関数）で取り出したキーの昇順に、範囲を **その場で** 安定に並べ替える。複数キーは `std::tie` でタプルを返す。

## Signature

```cpp
constexpr std::ranges::borrowed_iterator_t<R> std::ranges::stable_sort(R&& r, Comp comp = {}, Proj proj = {})
```

## Usage

```cpp
#include <algorithm>
#include <string>
#include <tuple>
#include <vector>

struct Row { std::string g; int v; };
std::vector<Row> rows{{"b", 2}, {"a", 9}, {"b", 1}};
std::ranges::stable_sort(rows, {}, [](const Row& r) { return std::tie(r.g, r.v); });
// rows => {"a", 9}, {"b", 1}, {"b", 2}
```

## Contract

- 安定ソート。キーが等しい要素は元の相対順を保つ（`ranges::greater{}` で降順にしても保つ）
- **in place**。範囲そのものを並べ替え、返り値は範囲の末尾イテレータ（右辺値の非 borrowed 範囲を渡すと `ranges::dangling`）
- 即時評価
- 複数キーはプロジェクションで `std::tie(a, b)` を返す。左から順に比較し、前が等しいときだけ次で比較する
- プロジェクションは各要素につき 1 回ではなく **比較のたびに** 呼ばれる。回数は実装依存だが要素数より多くなりうるので、重いキー計算は事前に別の配列へ出す
- 比較子の既定は `ranges::less`。比較子は strict weak ordering であること（`<=` や NaN を含む `double` は要件違反で未定義動作）
- メンバへのポインタ `&Row::g` や const メンバ関数 `&Row::key` をそのままプロジェクションに渡せる
- random_access_range が必要（`vector`、`deque`、配列）。`list` はコンパイルエラーになるので `list::sort` を使う
- 空の範囲でも動く

## Alternatives

- 安定性が要らないなら `ranges::sort`（同じキーの要素の順序は保証されない）
- キーごとに向きを変えるなら比較子を書くか、安定性を利用して **後ろのキーから順に** `stable_sort` を複数回かける
- 非破壊で新しい `vector` が欲しいなら `auto sorted = rows; ranges::stable_sort(sorted, ...)`（`toSorted` 相当は無い）
- C++17 以前は `std::stable_sort(v.begin(), v.end(), comp)`（プロジェクション引数は無い）
- 最小・最大の 1 件だけなら `ranges::min_element(v, {}, proj)`

## Pitfalls

- es-toolkit の `sortBy` や Python の `sorted` は新しい配列を返すが、C++ は in place。元を残したいならコピーしてから
- `std::tie` はプロジェクションが受け取った要素への参照の tuple を返す。ラムダ引数を値で受ける（`[](Row r)`）とダングリングになるので `const Row&` で受ける
- es-toolkit の `sortBy` は `null` / `undefined` を末尾に置くが、C++ の `std::optional` は `nullopt` が最小で **先頭** に来る
- `double` の NaN は strict weak ordering を壊す。事前に除くか `std::isnan` で振り分ける
- 文字列は `std::string` の `<`（バイト順）で、大文字が小文字より前。大小を無視するなら小文字化した文字列をキーにする

## Test

`examples/collection-sort-by_test.cpp`
