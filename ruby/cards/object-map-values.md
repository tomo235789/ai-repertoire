---
id: object-map-values
lang: ruby
title: オブジェクトの各値を変換して同じキーの新しいオブジェクトを作る
tags: [値の変換, ハッシュの変換, ハッシュのmap, map-values, transform, transform-values, dictionary]
lib: stdlib
fn: Hash#transform_values
since: "2.4"
verified: 2026-09-17
preserves_order: true
status: public
---

キーはそのままに、各値だけをブロックで変換した新しいハッシュを作る。`Hash[Symbol, X]` を `Hash[Symbol, Y]` に変換するときに使う。

## Signature

```ruby
hash.transform_values { |value| ... } -> new_hash
```

## Usage

```ruby
scores = { alice: [80, 90], bob: [70] }
scores.transform_values { |list| list.length }
# => {alice: 2, bob: 1}
scores.transform_values(&:sum)
# => {alice: 170, bob: 70}
```

## Contract

- キーの順序を保持する。返り値のキーは入力と同じ
- 入力ハッシュを変更しない。返り値は新しい `Hash`。ブロックが返した値がそのまま入る（入力の値を返せば同じオブジェクト）
- ブロックは純粋関数であること。各キーにつきちょうど 1 回、値だけを引数に挿入順に呼ばれる（キーは渡されない）
- 空のハッシュを渡すと `{}` を返す
- 元のハッシュの `default` / `default_proc` は返り値に引き継がれない（`compare_by_identity` は引き継がれる）
- ブロック無しで呼ぶと `Enumerator` を返す
- 例外は投げない（ブロックが投げた例外はそのまま伝播する）

## Alternatives

- 元のハッシュを書き換えてよいなら `transform_values!`（返り値は `self`）
- キーも変えるなら `transform_keys` か、キーと値を同時に扱う `hash.to_h { |k, v| [k.to_s, v * 2] }`。キーが衝突すると後勝ち
- キーと値の両方を使って値を決めるなら `hash.to_h { |k, v| [k, f(k, v)] }`
- 配列の各要素を変換するなら `Array#map`（`Hash#map` は配列を返す）

## Pitfalls

- TypeScript 版（es-toolkit の `mapValues`）、Python の `{k: f(v) for k, v in d.items()}` と同じ意味論。ただしブロックにキーは渡されない。キーが要るなら `to_h { |k, v| ... }`
- `hash.map { |k, v| [k, f(v)] }` は配列の配列を返す。ハッシュに戻すには `.to_h` が要る
- `transform_values` は値を差し替えるだけなので、返した値が入力と同じオブジェクト（`&:itself`）なら浅いコピーと変わらない。ネストしたハッシュは共有される

## Test

`examples/object-map-values_test.rb`
