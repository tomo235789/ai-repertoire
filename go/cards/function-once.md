---
id: function-once
lang: go
title: 関数を 1 回だけ実行する
tags: [一度だけ, 初回のみ, 初期化, 遅延初期化, once, single-call, lazy-init]
lib: stdlib
fn: sync.OnceValue
since: "1.21"
verified: 2026-09-17
status: public
---

最初の呼び出しだけ関数を実行し、以後は最初の戻り値を返し続ける。設定の読み込みやクライアントの初期化を 1 回に限定するのに使う。goroutine 安全。

## Signature

```go
func OnceValue[T any](f func() T) func() T
```

## Usage

```go
import ("fmt"; "sync")

loadConfig := sync.OnceValue(func() map[string]string {
	fmt.Println("load")
	return map[string]string{"mode": "test"}
})
a := loadConfig() // "load" が出る
b := loadConfig() // 何も出ない。a と同じマップが返る
// a と b は同じマップを指す
```

## Contract

- 1 回目の呼び出しで `f` を実行し、戻り値を保存する。2 回目以降は `f` を呼ばず **1 回目の戻り値（同じ値・同じ参照）** を返す
- 返された関数は複数の goroutine から同時に呼んでも `f` は 1 回だけ実行され、他の呼び出しは完了を待つ
- `f` が panic すると、以後の呼び出しも **同じ値で panic し続ける**。`f` は再実行されない
- 状態は `OnceValue` の返り値ごとに持つ。別々に作れば独立
- `f` に `nil` を渡すと作成時ではなく最初の呼び出し時に nil pointer dereference で panic する
- `f` は引数を取れない。引数ごとにキャッシュしたいならカード function-memoize

## Alternatives

- `(T, error)` を返す初期化なら `sync.OnceValues`。エラーもキャッシュされ、2 回目以降も同じ `error` が返る（再試行されない）
- 戻り値が要らないなら `sync.OnceFunc`。構造体のフィールドとして持つなら `sync.Once` の `Do`
- 失敗時に再試行したいなら、`sync.Mutex` で成功時だけ結果を保存する自前の関数を書く

## Pitfalls

- 例外時の扱いが 3 言語で違う。TypeScript（es-toolkit の `once`）は例外を投げた初期化を「実行済み」として `undefined` を返し、Python（`functools.cache`）は再実行するが、Go は同じ panic を再現する。失敗が起こりうる初期化は `OnceValues` でエラーを返す設計にする（それでもエラーはキャッシュされる）
- 戻り値のマップ・スライス・ポインタは全呼び出しで共有される。呼び出し側で変更すると他にも影響する
- Go 1.21 未満では `sync.Once` と変数を組み合わせて書く

## Test

`examples/function-once_test.go`
