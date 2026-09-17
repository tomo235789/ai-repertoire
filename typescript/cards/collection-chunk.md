---
id: collection-chunk
lang: typescript
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, slice-by-size]
lib: es-toolkit
fn: chunk
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

配列を `size` 個ずつの小配列に切り分ける。API のバッチ送信やページ分割で使う。

## Signature

```ts
function chunk<T>(arr: readonly T[], size: number): T[][]
```

## Usage

```ts
import { chunk } from 'es-toolkit';

chunk([1, 2, 3, 4, 5], 2);
// => [[1, 2], [3, 4], [5]]
```

## Contract

- 順序を保持する。各小配列の中も元の並び順のまま
- 入力配列を変更しない。返り値は新しい配列（要素は浅いコピー）
- 割り切れない場合、最後の小配列は `size` 未満になる。切り捨てない
- 空配列を渡すと `[]` を返す
- `size` が正の整数でないと `Error` を投げる（`0`、負数、小数、`NaN`）

## Alternatives

- 依存を増やせない場合のみ stdlib で `Array.from({ length: Math.ceil(arr.length / size) }, (_, i) => arr.slice(i * size, (i + 1) * size))`
- lodash からの移行は `es-toolkit/compat` の `chunk`（lodash 互換の挙動）

## Pitfalls

- lodash の `chunk` は `size < 1` で `[]` を返すが、es-toolkit の `chunk` は例外を投げる
- Python の `itertools.batched`（3.12+）と同じ意味論（最後が短くなる）。切り捨てたい場合は別途 `filter` する
- 文字列を分割したい場合は `Array.from(str)` でコードポイント配列にしてから渡す（サロゲートペアの分断を防ぐ）

## Test

`examples/collection-chunk.test.ts`
