---
id: function-memoize
lang: csharp
title: 関数の戻り値を引数ごとにキャッシュする
tags: [メモ化, キャッシュ, 計算結果の再利用, memoize, memoization, cache, memo]
lib: stdlib
fn: ConcurrentDictionary.GetOrAdd
since: "6.0"
verified: 2026-09-17
status: public
---

同じ引数での呼び出し結果を `ConcurrentDictionary` に保存し、2 回目以降は関数を実行せずに返す。重い純粋関数（パース・集計・正規化）の再計算を避けるのに使う。

## Signature

```csharp
public TValue GetOrAdd(TKey key, Func<TKey, TValue> valueFactory)
```

## Usage

```csharp
using System.Collections.Concurrent;

var cache = new ConcurrentDictionary<int, double>();
double Area(int r) => cache.GetOrAdd(r, key => { Console.WriteLine("calc"); return Math.PI * key * key; });

Area(2);       // "calc" が出て 12.566...
Area(2);       // キャッシュから 12.566...（"calc" は出ない）
cache.Clear(); // キャッシュを消す
```

## Contract

- キーは `key` 引数そのもの。複数の引数をキーにするならタプル `(a, b)` にまとめる（値で比較される）
- キーの比較は `EqualityComparer<TKey>.Default`（コンストラクタで `IEqualityComparer<TKey>` を差し替えられる）。`double.NaN` 同士は等しい扱い
- キーが無いときだけ `valueFactory` を呼び、戻り値を保存してから返す。同じキーの 2 回目は呼ばない
- `valueFactory` が例外を投げた場合は保存せず例外が伝播する。次回また呼ばれる
- 辞書の操作はスレッド安全だが、`valueFactory` はロックの外で呼ばれる。同じキーで同時に呼ばれると **`valueFactory` は複数回実行され得る**。保存されるのは最初に書き込んだ 1 つで、全員に同じ値が返る
- `valueFactory` が返した `null` も値として保存される（次回は `valueFactory` を呼ばず `null` を返す）
- `key` か `valueFactory` が `null` なら `ArgumentNullException`。上限は無く、消すには `TryRemove` / `Clear`

## Alternatives

- 高コストな計算を厳密に 1 回にしたいなら値を `Lazy<T>` にする定石: `cache.GetOrAdd(key, k => new Lazy<T>(() => Compute(k))).Value`（カード function-once）。`GetOrAdd` が複数回呼ばれても `Lazy` が最初の 1 つに絞る
- 定数を入れるだけなら `GetOrAdd(key, value)`。クロージャの割り当てを避けたいなら `GetOrAdd(key, static (k, arg) => ..., arg)`
- 単一スレッドなら `Dictionary<TKey, TValue>` と `TryGetValue` で十分
- サイズ上限や TTL が要るなら `Microsoft.Extensions.Caching.Memory` の `MemoryCache.GetOrCreate`

## Pitfalls

- TypeScript（es-toolkit の `memoize`）は第 1 引数だけをキーにするが、C# は渡したキーがすべて。Python の `functools.cache` は全引数をキーにするので、タプルキーにすれば同じ意味論になる
- `Task<T>` を値にすると失敗した `Task` もキャッシュされ、以後ずっと同じ例外が返る。失敗時は `TryRemove` するか、成功結果だけを入れる
- キャッシュは無制限に増える。ユーザー入力など値域が広い引数をキーにするとメモリリークになる
- 非純粋な関数（時刻や乱数、外部状態に依存）をメモ化すると古い値を返し続ける

## Test

`examples/FunctionMemoizeTests.cs`
