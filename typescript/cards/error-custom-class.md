---
id: error-custom-class
lang: typescript
title: 独自のエラー型を定義する
tags: [独自エラー, エラークラス, 例外の種類分け, 継承, custom-error, class, extends-Error, instanceof]
lib: stdlib
fn: class extends Error
since: "ES2022"
verified: 2026-09-17
status: public
---

`Error` を継承したクラスに `name` と固有のプロパティを持たせ、`instanceof` で種類を判定できるようにする。HTTP エラーや検証エラーを呼び出し側で区別するために使う。

## Signature

```ts
class MyError extends Error { constructor(message?: string, options?: { cause?: unknown }) }
// Error.captureStackTrace(target: object, constructorOpt?: Function): void  — V8 のみ
```

## Usage

```ts
class HttpError extends Error {
  constructor(public readonly status: number, message = `HTTP ${status}`, options?: ErrorOptions) {
    super(message, options);
    this.name = 'HttpError'; // 設定しないと 'Error' のまま
  }
}
const err = new HttpError(404, undefined, { cause: new Error('row not found') });
err instanceof HttpError; // => true（tsconfig の target が ES2015 以上のとき）
String(err);              // => 'HttpError: HTTP 404'
err.stack?.split('\n')[0]; // => 'HttpError: HTTP 404'（先頭行は name: message）
```

## Contract

- `super(message, { cause })` で `message` と `cause` が設定される。`cause` は `options` に渡したときだけ自身のプロパティになる（列挙されない）
- `name` は既定で `'Error'`。サブクラスを作っても自動では変わらないので、コンストラクタで `this.name = 'HttpError'` と代入する。`toString()`（`String(err)`）と `stack` の先頭行は `name: message` になる
- `this.name = ...` で付けた `name` は **列挙可能な自身のプロパティ** になり、`JSON.stringify(err)` に現れる。`message` / `stack` は列挙されないので現れない
- `instanceof` はプロトタイプ連鎖で判定する。TypeScript の `target` が `ES5` だと `super()` の戻りで `this` のプロトタイプが `Error.prototype` になり、`err instanceof HttpError` が `false` になる。`ES2015` 以上では正しく動く
- `Error.captureStackTrace(err, fn)` は `stack` から `fn` とそれより内側のフレームを取り除く。クラス構文のコンストラクタは Node 26 では元々 `stack` に現れないので、`createHttpError()` のようなファクトリ関数のフレームを隠すときに使う。V8（Node / Chrome）にしか無いので `Error.captureStackTrace?.(...)` と書く
- `util.inspect`（`console.log`）は `stack` と、`status` のような列挙可能な自身のプロパティ、`[cause]` を表示する

## Alternatives

- 種類が増えたら `static is(e: unknown): e is HttpError` を用意して `instanceof` の分岐を集約する
- 型で判別したいだけなら `{ kind: 'http'; status: number }` のようなユニオン（判別可能な共用体）でも足りる。`Error` を継承すると `stack` が付き `throw` できる点が違い
- 原因を持たせて包み直す使い方はカード error-cause-chain

## Pitfalls

- `target: ES5` で `instanceof` が効かない場合は `super()` の直後に `Object.setPrototypeOf(this, new.target.prototype)` を足す。`ES2015` 以上なら不要
- `name` を `this.constructor.name` で付けると minify で `'a'` のような名前になる。文字列リテラルで書く
- `class ValidationError extends Error {}` だけだと `name` は `'Error'` で、ログや `stack` で区別できない
- `message` に本文以外（オブジェクト）を渡すと文字列化される。構造化データは `status` のようなプロパティに持たせる
- `JSON.stringify(err)` は `message` / `stack` / `cause` を落とす。ログに出すには明示的に展開する（カード log-structured）

## Test

`examples/error-custom-class.test.ts`
