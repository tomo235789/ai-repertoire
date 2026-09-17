---
id: collection-zip
lang: ruby
title: 複数の配列を要素ごとに組にする
tags: [組にする, 対応付け, 並行走査, zip, pair, tuple, transpose]
lib: stdlib
fn: Array#zip
since: "2.7"
verified: 2026-09-17
preserves_order: true
status: public
---

レシーバの各要素を、引数の同じ位置の要素と組にする。ヘッダー行と値の対応付けや 2 列の並行走査に使う。

## Signature

```ruby
zip(*other_arrays) -> new_array / zip(*other_arrays) { |sub_array| ... } -> nil
```

## Usage

```ruby
[1, 2, 3].zip(["a", "b", "c"])
# => [[1, "a"], [2, "b"], [3, "c"]]

[1, 2, 3].zip(["a", "b"])
# => [[1, "a"], [2, "b"], [3, nil]]  レシーバの長さに合わせる
```

## Contract

- 順序を保持する。i 番目の組は各配列の i 番目の要素からなる
- レシーバも引数も変更しない。各組は新しい配列で、要素は同じ参照
- 返り値の長さは **レシーバ** の長さ。引数が短ければ足りない位置は `nil`、引数が長ければ余りは切り捨てる
- 引数は可変長で、組の長さは `1 + 引数の数`。引数無しなら各要素を 1 要素の配列で包む
- 引数は配列でなくてもよく、`each` を持つオブジェクト（Range、Enumerator）ならレシーバの長さ分だけ読み進める。`each` を持たない値は `TypeError`
- ブロック付きなら各組をブロックに渡し、`nil` を返す
- レシーバが空なら `[]` を返す。ブロック付きなら空でも `nil`

## Alternatives

- 組にした後で `Hash` にするなら `keys.zip(values).to_h`
- 逆操作（組の配列を列の組に戻す）は `transpose`（長さが揃っていないと `IndexError`）
- 添字と組にするなら `each_with_index` / `each.with_index(1)`
- レシーバが配列でなくても `Enumerable#zip` が同じ意味論で使える

## Pitfalls

- es-toolkit の `zip` は **最も長い** 配列に合わせ、Python の `zip` は **最も短い** 入力で打ち切るが、Ruby は **レシーバ** の長さに合わせる。引数側の余りは黙って捨てられ、不足は `nil` で埋まる。長さが違いうるときは呼び出し側で検査する
- ブロック付きの返り値は `nil`。組の配列が欲しいならブロックを付けない
- 要素に `nil` が含まれる場合、埋められた `nil` と区別できない。区別が要るなら先に長さを比べる

## Test

`examples/collection-zip_test.rb`
