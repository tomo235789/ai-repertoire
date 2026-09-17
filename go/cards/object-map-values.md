---
id: object-map-values
lang: go
title: オブジェクトの各値を変換して同じキーの新しいオブジェクトを作る
tags: [値の変換, マップの変換, map-values, transform, dictionary, mapping]
lib: samber/lo
fn: lo.MapValues
since: "1.7.0"
verified: 2026-09-17
status: public
---

map の各値を関数で変換し、同じキーを持つ新しい map を作る。設定値の正規化や表示用の整形に使う。

## Signature

```go
func MapValues[K comparable, V, R any](in map[K]V, iteratee func(value V, key K) R) map[K]R
```

## Usage

```go
import ("fmt"; "github.com/samber/lo")

prices := map[string]int{"apple": 100, "pear": 250}
lo.MapValues(prices, func(v int, k string) string { return fmt.Sprintf("%d円", v) })
// => map[string]string{"apple": "100円", "pear": "250円"}
```

## Contract

- 返り値のキー集合は入力と同じ
- 入力 map を変更しない。返り値は新しい `map[K]R`。`iteratee` が返した値がそのまま入る（入力の値を返せばポインタやスライスは同じ参照先を指す）
- `iteratee` は `(value, key)` の順で受け取る。純粋関数であること。各エントリにつきちょうど 1 回呼ばれるが、呼ばれる順は map の走査順で **不定**
- 空・nil の map を渡すと空の非 nil map（`len == 0`）を返す
- 返り値の型は常に `map[K]R`。入力が名前付き map 型でも返り値には引き継がれない
- panic しない

## Alternatives

- キーを変えるなら `lo.MapKeys`、キーと値を同時に変えるなら `lo.MapEntries`
- 値の型が変わらず元の map を書き換えてよいなら stdlib で `for k, v := range m { m[k] = f(v) }`
- stdlib の `maps` パッケージにこの操作は無い。依存を増やせない場合は `out := make(map[K]R, len(m))` に詰めるループ
- スライスの各要素を変換するなら `lo.Map`

## Pitfalls

- 引数の順は `(value, key)`。es-toolkit の `mapValues` と同じだが、Python の `d.items()` の `(k, v)` とは逆
- `iteratee` は map の走査順で呼ばれるので、呼び出し順に依存する副作用（連番の採番など）を入れると実行ごとに結果が変わる
- `Map ~map[K]V` の型引数を取らないため、名前付き map 型（`type Config map[string]string`）を渡しても返り値は素の `map[string]string`。必要なら変換する

## Test

`examples/object-map-values_test.go`
