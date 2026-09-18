---
id: object-invert
lang: ruby
title: オブジェクトのキーと値を入れ替える
tags: [逆引き, キーと値の交換, 逆マッピング, invert, reverse-map, swap-keys, lookup]
lib: stdlib
fn: Hash#invert
since: "1.9"
verified: 2026-09-17
preserves_order: true
status: public
---

キーと値を入れ替えた新しいハッシュを作る。コード → 名前の対応表から名前 → コードの逆引き表を作るときに使う。

## Signature

```ruby
hash.invert -> new_hash
```

## Usage

```ruby
code_to_name = { 1 => "red", 2 => "blue" }
code_to_name.invert
# => {"red" => 1, "blue" => 2}
```

## Contract

- 入力ハッシュを変更しない。返り値は新しい `Hash`
- 返り値のキーは元の値、返り値の値は元のキー。型はそのまま（文字列化しない）
- 順序は元のハッシュの挿入順
- 値が重複した場合は **最後** に処理されたキーが残る。返り値でのそのキーの位置は最初に出現した場所（`{ a: 1, b: 2, c: 1 }.invert` は `{1 => :c, 2 => :b}`）
- 値の同一性は `eql?` / `hash` で判定する。`1` と `1.0` は別のキーになる（`{ a: 1, b: 1.0 }.invert` は 2 要素）
- 値が配列やハッシュでもキーにできる。`nil` もキーにできる。例外は投げない
- 元のハッシュの `default` / `default_proc` / `compare_by_identity` は返り値に引き継がれない

## Alternatives

- 1 つの値からキーを引くだけなら `hash.key(value)`（最初に一致したキー。無ければ `nil`）か `hash.rassoc(value)`（`[key, value]` の組）
- 重複する値をまとめたい（`{1 => [:a, :b]}`）なら `hash.group_by { |k, v| v }.transform_values { |pairs| pairs.map(&:first) }`
- 重複を検出したいなら `hash.invert.size == hash.size` を確認する

## Pitfalls

- TypeScript 版（es-toolkit の `invert`）、Python の `{v: k for k, v in d.items()}` と同じで最後が残る。ただし es-toolkit は元のキーを文字列化し（`1` は `'1'`）、整数風のキーを昇順で先頭に並べる。Ruby は型も挿入順もそのまま
- Python は `1` と `1.0` と `True` を同じキーとみなすが、Ruby は `1` と `1.0` を区別する（`true` は別物）
- 値が配列などの可変オブジェクトのときも `TypeError` にならずキーになるが、キーにした後で中身を変えると `hash` 値が変わり `[]` で引けなくなる。`rehash` を呼ぶと引けるようになる。可変オブジェクトをキーにするなら先に `freeze` しておく

## Test

`examples/object-invert_test.rb`
