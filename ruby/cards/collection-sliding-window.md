---
id: collection-sliding-window
lang: ruby
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 移動平均, sliding-window, windowed, rolling, each-cons]
lib: stdlib
fn: Enumerable#each_cons
since: "3.1"
verified: 2026-09-17
preserves_order: true
status: public
---

幅 `n` の窓を 1 つずつずらしながら配列で取り出す。移動平均や隣接要素の比較に使う。

## Signature

```ruby
each_cons(n) { |window| ... } -> self / each_cons(n) -> Enumerator
```

## Usage

```ruby
[1, 2, 3, 4, 5].each_cons(3).to_a
# => [[1, 2, 3], [2, 3, 4], [3, 4, 5]]

[1, 2, 3, 4, 5].each_cons(2).map { |a, b| b - a }
# => [1, 1, 1, 1]
```

## Contract

- 順序を保持する。窓は先頭から 1 つずつずれた開始位置で並び、窓の中も元の並び順
- レシーバを変更しない。各窓は新しい配列（窓ごとに別オブジェクト）で、要素は同じ参照
- ブロック無しなら `Enumerator` を返し、`first(k)` などで必要な分だけ入力を読み進める。ブロック付きならレシーバ自身を返す（3.0 以前は `nil`）
- `n` に満たない末尾の窓は **出力しない**。要素数が `n` 未満なら何も yield せず `to_a` は `[]`
- `step` は指定できない。常に 1 つずつずれる
- 空配列なら何も yield しない
- `n` が `0` 以下なら `ArgumentError`。整数でない値は `to_int` で変換され（`1.5` → `1`）、変換できない値は `TypeError`

## Alternatives

- 重ならない分割は `each_slice(n)`（collection-chunk）。`each_cons` は重なる窓
- `step` 相当が欲しいなら `each_cons(n).each_slice(step).map(&:first)`（`step` ごとに 1 窓を残す）
- 末尾の短い窓も欲しいなら `(0...arr.size).map { |i| arr[i, n] }`
- 添字で切るなら `(0..arr.size - n).map { |i| arr[i, n] }`（`arr.size < n` なら終端が始端より小さい Range になり 1 度も繰り返さないので `[]`）

## Pitfalls

- es-toolkit の `windowed` の既定（`partialWindows: false`）と同じで末尾を捨てる。Python の `more_itertools.windowed` は `fillvalue` で埋めるので意味論が違う
- `each_slice(n)` と混同しやすい。`each_slice` は重ならず、最後の短い小配列も出す
- es-toolkit の `windowed` は `step` を取るが、`each_cons` には無い。`each_slice` との組み合わせで代用する

## Test

`examples/collection-sliding-window_test.rb`
