---
id: object-omit
lang: ruby
title: オブジェクトから指定したキーを除いたコピーを作る
tags: [除外, キー削除, 部分ハッシュ, omit, except, exclude-keys, drop-keys, without]
lib: stdlib
fn: Hash#except
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

ハッシュから不要なキーを除いた新しいハッシュを作る。パスワードなど外に出したくないフィールドの除去に使う。

## Signature

```ruby
hash.except(*keys) -> new_hash
```

## Usage

```ruby
user = { id: 1, name: "a", password: "x" }
user.except(:password)
# => {id: 1, name: "a"}
user.except(:password, :name)
# => {id: 1}
```

## Contract

- 入力ハッシュを変更しない。返り値は新しい `Hash`（値は浅いコピー。ネストしたハッシュや配列は同じオブジェクト）
- 残ったキーの順序は元のハッシュのまま
- 存在しないキーを指定しても無視される
- すべてのキーを除くと `{}`。引数無しなら元と同じ内容の別オブジェクト
- キーの一致は `Hash#[]` と同じ `eql?` / `hash` による。`"a"` と `:a` は別のキー
- 元のハッシュの `default` / `default_proc` は返り値に引き継がれない（`compare_by_identity` は引き継がれる）
- 例外は投げない

## Alternatives

- 条件で除くなら `hash.reject { |k, v| v.nil? }`（`select` / `filter_map` の裏返し）
- 残す側を列挙するなら `hash.slice(:id, :name)`（object-pick）
- 元のハッシュを破壊的に変えてよいなら `hash.delete(:password)`（存在しなくても失敗せず `nil` を返す）

## Pitfalls

- キーは可変長引数で渡す。配列を 1 つ渡すと `hash.except([:a])` は「配列 `[:a]` というキー」を探すので何も除かれない。配列を持っているなら `hash.except(*keys)` と展開する
- TypeScript 版（es-toolkit の `omit`）、Python の `{k: v for k, v in d.items() if k not in keys}` と同じ意味論。破壊的な `delete` は元を変えるので違う
- Ruby 2.7 以前には無い（ActiveSupport が同名のメソッドを提供していた）

## Test

`examples/object-omit_test.rb`
