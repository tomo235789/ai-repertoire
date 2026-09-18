---
id: json-stringify-stable
lang: typescript
title: オブジェクトをキー順を揃えた決定的な JSON 文字列にする
tags: [決定的な JSON, キーソート, ハッシュ用文字列, stringify, stable, deterministic, canonical]
lib: safe-stable-stringify
fn: stringify
since: "2.0"
verified: 2026-09-17
status: public
---

キーを全階層でソートし、同じ内容なら挿入順によらず同じ文字列を返す。循環参照と `bigint` でも例外を投げない。キャッシュキー・ハッシュ・スナップショット比較に使う。

## Signature

```ts
function stringify(value: unknown, replacer?: Replacer, space?: string | number): string | undefined  // stringify.configure(options) で挙動を変更
```

## Usage

```ts
import stringify from 'safe-stable-stringify';

stringify({ b: 1, a: { d: 2, c: 3 } });
// => '{"a":{"c":3,"d":2},"b":1}'（JSON.stringify なら '{"b":1,"a":{"d":2,"c":3}}'）
const self: Record<string, unknown> = { a: 1 };
self.self = self;
stringify(self);        // => '{"a":1,"self":"[Circular]"}'（JSON.stringify は TypeError）
stringify({ n: 10n });  // => '{"n":10}'（JSON.stringify は TypeError）
```

## Contract

- 全階層のオブジェクトのキーを文字列比較で昇順に並べる。配列の順序は変えない。内容が同じなら挿入順が違っても同じ文字列になる
- 循環参照は `"[Circular]"` 文字列に置き換える。同じオブジェクトへの複数参照（循環ではない）はそれぞれの場所に展開する
- `bigint` は数値リテラルとして出力する（`{"n":10}`）
- `undefined` / 関数 / symbol の扱いは `JSON.stringify` と同じ。プロパティなら省略、配列の要素なら `null`、トップレベルなら戻り値 `undefined`
- `NaN` / `Infinity` は `null`、`Date` は `toJSON`（ISO 文字列）、`Map` / `Set` は `{}`。これも `JSON.stringify` と同じ
- `toJSON` を持つ値は `toJSON` の戻り値をソートして出力する
- 第 2 引数 `replacer`（関数または許可キー配列）と第 3 引数 `space` は `JSON.stringify` と同じ意味
- `stringify.configure({ circularValue: Error })` で循環時に `TypeError` を投げる、`{ deterministic: false }` でソートしない、`{ bigint: false }` で `bigint` を省略する、など挙動を変えた関数を作れる

## Alternatives

- 順序が問題にならない（自分で作ったオブジェクトをその場で使う）なら `JSON.stringify` で十分
- 循環だけを避けたい場合も同じ関数でよい。`deterministic: false` にすれば `JSON.stringify` の順序のまま循環だけ処理する
- 比較だけが目的なら文字列にせず `isEqual`（カード json-deep-equal）

## Pitfalls

- 数値風のキー（`'2'`, `'10'`）の順序が `JSON.stringify` と違う。`JSON.stringify` は整数キーを数値順で先頭に置く（`{"2":3,"10":2,"b":1,"a":4}`）が、この関数は文字列比較で並べる（`{"10":2,"2":3,"a":4,"b":1}`）
- `"[Circular]"` は普通の文字列なので、`JSON.parse` で戻しても元の構造にはならない。循環を許したくないなら `configure({ circularValue: Error })`
- `bigint` が数値として出るので、`JSON.parse` で読み戻すと `Number` になり精度が落ちる（`9007199254740993n` → `9007199254740992`）
- ハッシュ用途では `space` を付けない。整形すると空白が入り別の文字列になる

## Test

`examples/json-stringify-stable.test.ts`
