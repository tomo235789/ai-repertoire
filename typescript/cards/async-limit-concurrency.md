---
id: async-limit-concurrency
lang: typescript
title: 非同期処理の同時実行数を制限する
tags: [同時実行数, 並列制限, セマフォ, 排他, concurrency-limit, semaphore, throttle-parallel, rate-limit]
lib: es-toolkit
fn: Semaphore
since: "1.32.0"
verified: 2026-09-17
status: public
---

同時に走らせる非同期処理の数を `capacity` までに抑える。API のレート制限やコネクション数の上限に合わせて並列度を絞るのに使う。

## Signature

```ts
class Semaphore { constructor(capacity: number); acquire(): Promise<void>; release(): void; capacity: number; available: number }
```

## Usage

```ts
import { Semaphore } from 'es-toolkit';

const sem = new Semaphore(2); // 同時に 2 つまで
async function fetchLimited(id: number) {
  await sem.acquire();
  try { return await fetchJson(`/api/items/${id}`); }
  finally { sem.release(); }
}
await Promise.all([1, 2, 3, 4].map(fetchLimited));
// => 常に 2 件以下しか同時に fetch されない
```

## Contract

- `acquire()` は空き（`available > 0`）があれば `available` を 1 減らして即 resolve する。空きが無ければ `release()` が呼ばれるまで待つ
- 待機は **呼び出し順（FIFO）** に解放される。`release()` は待機者がいれば先頭の 1 つを起こし（`available` は変わらない）、いなければ `available` を 1 増やす
- `available` は `capacity` を超えない。余分な `release()` は無視される
- `capacity` と `available` は公開プロパティで、現在の空き数を確認できる
- `acquire()` に制限時間や `AbortSignal` は無い。`release()` されるまで待ち続ける

## Alternatives

- 1 つの関数の呼び出しを制限するだけなら `limitAsync(fn, concurrency)`（es-toolkit）。`acquire` / `release` を書かずに済む
- 同時に 1 つだけ（排他）なら `Mutex`（es-toolkit。`isLocked` で状態を確認できる）
- タスク配列を並列度付きで流したいなら `p-limit` / `p-map`
- 依存を増やせない場合は `chunk`（カード collection-chunk）で分けて `Promise.all` を順に回す（バッチ内は並列、バッチ間は直列）

## Pitfalls

- `release()` を忘れると空きが戻らず、以後の `acquire()` は永久に待ち続ける。必ず `try { ... } finally { sem.release() }` で囲む
- `acquire()` せずに `release()` を余計に呼んでも例外は出ず、静かに無視される。呼び出しの対応が崩れていても気づきにくい
- `acquire()` に制限時間を付けたい場合、`withTimeout(() => pending, ms)` は reject しても `pending` を取り消さないので、後から permit が渡されて誰も `release()` しない状態になり得る。失敗時は `pending.then(() => sem.release())` で補償し、成功時は `finally` で `release()` する
- `limitAsync` と違い、`Semaphore` は制限だけでキューの順序保証以外の面倒（結果の収集・エラー処理）は見ない

## Test

`examples/async-limit-concurrency.test.ts`
