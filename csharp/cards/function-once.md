---
id: function-once
lang: csharp
title: 関数を 1 回だけ実行する
tags: [一度だけ, 初回のみ, 初期化, 遅延初期化, once, single-call, lazy-init]
lib: stdlib
fn: Lazy<T>
since: "6.0"
verified: 2026-09-17
status: public
---

最初に `.Value` を読んだときだけ関数を実行し、以後は最初の戻り値を返し続ける。初期化処理や設定の読み込みを 1 回に限定するのに使う。

## Signature

```csharp
public Lazy(Func<T> valueFactory)
```

## Usage

```csharp
using System;

var init = new Lazy<string>(() => { Console.WriteLine("init"); return "config"; });
init.IsValueCreated;   // => false（まだ呼ばれない）
var a = init.Value;    // "init" が出る
var b = init.Value;    // 何も出ない。同じ値が返る
ReferenceEquals(a, b); // => true
```

## Contract

- 最初の `.Value` で `valueFactory` を 1 回だけ実行し、戻り値を保存する。2 回目以降は呼ばず **同じ参照** を返す。引数は渡せない
- 既定の `LazyThreadSafetyMode.ExecutionAndPublication` はスレッド安全。複数スレッドが同時に `.Value` を読んでも `valueFactory` は 1 回だけ実行され、他のスレッドは完了を待つ
- `valueFactory` が例外を投げると **例外もキャッシュされ**、以後の `.Value` は `valueFactory` を呼ばずに同じ例外インスタンスを投げ続ける。`IsValueCreated` は `false` のまま
- `LazyThreadSafetyMode.PublicationOnly` は例外をキャッシュせず次回再実行する。同時アクセスでは複数スレッドが `valueFactory` を実行し得るが、公開される値は 1 つ
- `LazyThreadSafetyMode.None` はスレッド安全でない（単一スレッド専用）。例外はキャッシュされる
- `valueFactory` の中で自身の `.Value` を読むと `InvalidOperationException`（既定モード）
- `valueFactory` が `null` なら `ArgumentNullException`。`IsValueCreated` で実行済みかを確認できる

## Alternatives

- 失敗した初期化をやり直したいなら `new Lazy<T>(factory, LazyThreadSafetyMode.PublicationOnly)`
- 非同期の初期化を 1 回にしたいなら `Lazy<Task<T>>`（1 回目の `Task` が共有される。失敗した `Task` もキャッシュされる）
- 引数ごとに結果を使い回したいなら `ConcurrentDictionary.GetOrAdd`（カード function-memoize）
- フィールドを遅延初期化するだけなら `LazyInitializer.EnsureInitialized(ref field, factory)`

## Pitfalls

- TypeScript（es-toolkit の `once`）は例外を投げた初期化も「実行済み」にして以後 `undefined` を返し、Python の `functools.cache` は例外を保存せず再試行する。`Lazy<T>` はどちらとも違い、**同じ例外を投げ続ける**。一時的な失敗（ネットワーク）を含む初期化には `PublicationOnly` を使う
- `PublicationOnly` は `valueFactory` が複数回走る前提で書く。副作用のある初期化（接続を開く、ファイルを作る）には向かない
- `PublicationOnly` は再帰（`valueFactory` 内で自身の `.Value` を読む）を検出しない
- `.Value` を読まなければ実行されない。「起動時に必ず走らせたい」なら明示的に読む

## Test

`examples/FunctionOnceTests.cs`
