---
id: object-omit
lang: typescript
title: オブジェクトから指定したキーを除いたコピーを作る
tags: [除外, キー削除, 部分オブジェクト, omit, exclude-keys, drop-keys, without]
lib: es-toolkit
fn: omit
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

オブジェクトから不要なキーを除いた新しいオブジェクトを作る。パスワードなど外に出したくないフィールドの除去に使う。

## Signature

```ts
function omit<T extends Record<string, any>, K extends keyof T>(obj: T, keys: readonly K[]): Omit<T, K>
```

## Usage

```ts
import { omit } from 'es-toolkit';

const user = { id: 1, name: 'a', password: 'x' };
omit(user, ['password']);
// => { id: 1, name: 'a' }
```

## Contract

- 入力オブジェクトを変更しない。返り値はスプレッド（`{ ...obj }`）で作った新しいオブジェクトから `delete` したもの。値は浅いコピーで、ネストしたオブジェクトは同じ参照
- 自身の列挙可能なプロパティだけがコピーされる。継承したプロパティは返り値に含まれない。シンボルキーは含まれる
- 残ったキーの順序は元オブジェクトのまま
- 存在しないキーを指定しても無視される
- すべてのキーを除くと `{}`。`keys` が空なら元と同じ内容の浅いコピー
- 例外は投げない

## Alternatives

- 条件で除くなら `omitBy(obj, (value, key) => ...)`（`undefined` の値を落とすなど）
- 残す側を列挙するなら `pick`（object-pick）
- キーが静的に決まるなら stdlib の分割代入 `const { password, ...rest } = user`
- lodash からの移行は `es-toolkit/compat` の `omit`（可変長引数とパス指定が使える）

## Pitfalls

- lodash の `omit` は継承した列挙可能プロパティもコピーするが、es-toolkit は自身のプロパティだけ
- 型は `K extends keyof T` なので、`T` に無いキーを渡すとコンパイルエラーになる。動的なキー配列は `obj` の型を広げる
- Python の `{k: v for k, v in d.items() if k not in keys}` と同じ意味論。`del d[k]` は元を変えるので違う

## Test

`examples/object-omit.test.ts`
