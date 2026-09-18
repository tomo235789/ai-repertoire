---
id: object-pick
lang: ruby
title: オブジェクトから指定したキーだけを取り出す
tags: [抽出, キー選択, 部分ハッシュ, pick, select-keys, subset, slice]
lib: stdlib
fn: Hash#slice
since: "2.5"
verified: 2026-09-17
preserves_order: true
status: public
---

`Hash` から必要なキーだけを持つ新しい `Hash` を作る。API レスポンスの整形や、機密フィールドを含まない DTO の作成に使う。

## Signature

```ruby
slice(*keys) -> new_hash
```

## Usage

```ruby
user = { id: 1, name: "a", password: "x" }
user.slice(:name, :id, :missing)
# => {name: "a", id: 1}
```

## Contract

- レシーバを変更しない。返り値は新しい `Hash`（値は浅いコピー。ネストしたハッシュや配列は同じ参照）
- 存在しないキーは無視され、返り値にそのキーは作られない。値が `nil` のキーは `nil` のまま含まれる
- 返り値のキーは **引数の並び順**（元の `Hash` の順ではない）。引数に重複があっても 1 つにまとまる
- キーの比較は元の `Hash` と同じ（`hash` と `eql?`。`compare_by_identity` なら同一性）。`1` で `1.0` は取れず、`"a"` で `:a` は取れない
- 引数が無い、または該当するキーが 1 つも無ければ `{}` を返す
- 返り値にデフォルト値・デフォルトブロックは引き継がれない（`compare_by_identity` は引き継がれる）
- 例外は投げない

## Alternatives

- 条件で選ぶなら `select { |k, v| ... }`（返り値は `Hash`、キーは元の順）
- 除外する側を列挙したいなら `except(*keys)`（3.0 以降。object-omit）
- 値だけを配列で取り出すなら `values_at(*keys)`（無いキーは `nil`）、無いキーで失敗させたいなら `fetch_values(*keys)`（`KeyError`）
- キーを変えながら選ぶなら `filter_map { |k, v| [new_key, v] if cond }.to_h`

## Pitfalls

- 引数は可変長。キーの配列を持っているなら `h.slice(*keys)` と splat する。`h.slice(keys)` は配列 1 つをキーとして探すので `{}` になる
- ActiveSupport の `Hash#slice!`（指定キー **以外** を削除して、削除した分を返す）は Ruby 本体には無い。素の Ruby では `NoMethodError`
- es-toolkit の `pick` は整数風のキーが昇順で先頭に並ぶが、Ruby は引数の順のまま。Python の `{k: d[k] for k in keys}` は無いキーで `KeyError` になるが、`slice` は黙って無視する
- 文字列キーとシンボルキーは別物。JSON を `JSON.parse` した `Hash` は文字列キーなので `slice("id")` と書く（`symbolize_names: true` なら `:id`）

## Test

`examples/object-pick_test.rb`
