---
id: object-pick
lang: typescript
title: オブジェクトから指定したキーだけを取り出す
tags: [抽出, キー選択, 部分オブジェクト, pick, select-keys, subset, projection]
lib: es-toolkit
fn: pick
since: "1.0.0"
verified: 2026-09-17
status: public
---

オブジェクトから必要なキーだけを持つ新しいオブジェクトを作る。API レスポンスの整形や、機密フィールドを含まない DTO の作成に使う。

## Signature

```ts
function pick<T extends Record<string, any>, K extends keyof T>(obj: T, keys: readonly K[]): Pick<T, K>
```

## Usage

```ts
import { pick } from 'es-toolkit';

const user = { id: 1, name: 'a', password: 'x' };
pick(user, ['id', 'name']);
// => { id: 1, name: 'a' }
```

## Contract

- 入力オブジェクトを変更しない。返り値は新しいオブジェクト（値は浅いコピー。ネストしたオブジェクトは同じ参照）
- 自身のプロパティ（`Object.hasOwn`）だけを対象にする。継承したプロパティは取り出せない
- 存在しないキーは無視され、返り値にそのキーは作られない。値が `undefined` の自身のプロパティは `undefined` のまま含まれる
- 返り値のキーは `keys` の並び順で入るが、整数風のキー（`'1'`、`2` など）は通常のオブジェクトの列挙規則により昇順で先頭に並ぶ。`keys` に重複があっても 1 つにまとまる
- `keys` が空なら `{}` を返す
- 例外は投げない

## Alternatives

- 条件で選ぶなら `pickBy(obj, (value, key) => ...)`
- 除外する側を列挙したいなら `omit`（object-omit）
- lodash からの移行は `es-toolkit/compat` の `pick`（可変長引数と `'a.b'` のようなパス指定が使える）
- 依存を増やせない場合のみ stdlib で `Object.fromEntries(keys.filter((k) => Object.hasOwn(obj, k)).map((k) => [k, obj[k]]))`

## Pitfalls

- 自身のキー `'__proto__'` は通常の代入で作られるため、返り値に自身のプロパティとして残らない（値がオブジェクトなら返り値のプロトタイプが変わる）。外部入力由来のキー配列をそのまま渡さない（`'__proto__'` を除外するか、`Object.create(null)` に自前で詰め直す）

- lodash の `pick(obj, 'a', 'b')` のような可変長指定や `'a.b'` のパス指定は不可。キーの配列を渡す
- 型は `K extends keyof T` なので、`T` に無いキーを渡すとコンパイルエラーになる。動的なキー配列を渡すときは `obj` を `Record<string, unknown>` などに広げる
- Python の `{k: d[k] for k in keys}` は存在しないキーで `KeyError` になるが、es-toolkit は黙って無視する

## Test

`examples/object-pick.test.ts`
