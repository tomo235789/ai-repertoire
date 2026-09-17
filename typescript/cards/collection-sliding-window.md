---
id: collection-sliding-window
lang: typescript
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 連続部分列, sliding-window, windowed, rolling, moving]
lib: es-toolkit
fn: windowed
since: "1.31.0"
verified: 2026-09-17
preserves_order: true
status: public
---

固定長 `size` の窓を `step` ずつずらしながら部分配列を切り出す。移動平均や隣接要素の比較に使う。

## Signature

```ts
function windowed<T>(arr: readonly T[], size: number, step?: number, { partialWindows }?: WindowedOptions): T[][]
```

## Usage

```ts
import { windowed } from 'es-toolkit';

windowed([1, 2, 3, 4, 5], 3);
// => [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
windowed([1, 2, 3, 4, 5], 3, 2, { partialWindows: true });
// => [[1, 2, 3], [3, 4, 5], [5]]
```

## Contract

- 順序を保持する。窓は先頭から `step` 刻みの開始位置で並び、窓の中も元の並び順
- 入力配列を変更しない。各窓は `slice` で作った新しい配列（要素は同じ参照）
- `step` の既定値は `1`。`step > size` なら窓の間の要素は飛ばされる
- `partialWindows` の既定値は `false`。`size` に満たない末尾の窓は **捨てられ**、配列長が `size` 未満なら `[]` を返す
- `partialWindows: true` なら開始位置が配列内にある窓をすべて返し、末尾の窓は `size` より短くなりうる
- 空配列を渡すと `[]` を返す
- `size` または `step` が正の整数でないと `Error` を投げる（`0`、負数、小数、`NaN`）

## Alternatives

- 依存を増やせない場合のみ stdlib で `Array.from({ length: Math.max(0, arr.length - size + 1) }, (_, i) => arr.slice(i, i + size))`
- 重ならない分割は `chunk(arr, size)`（`windowed(arr, size, size, { partialWindows: true })` と同じ結果）

## Pitfalls

- lodash に相当する関数は無い。引数の形は Kotlin の `windowed(size, step, partialWindows)` と同じ
- Python の `itertools.pairwise`（3.10+）は `windowed(arr, 2)` に相当する。`more_itertools.windowed` は足りない分を `fillvalue` で埋めるが、es-toolkit は捨てるか短い窓を返すかの二択
- `chunk` と違い既定では末尾を捨てる。要素を取りこぼしたくないなら `partialWindows: true` を明示する

## Test

`examples/collection-sliding-window.test.ts`
