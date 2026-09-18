---
id: log-redact-secrets
lang: typescript
title: ログから秘密情報をマスクする
tags: [秘密情報のマスク, 機密情報, パスワード, トークン, ログの伏せ字, redact, mask, sensitive-data, secrets]
lib: stdlib
fn: 純粋関数
since: "ES2015"
verified: 2026-09-17
status: public
---

オブジェクトを再帰的に辿り、`password` / `token` / `authorization` などのキーに入っている値を `"[REDACTED]"` に置き換えた新しいオブジェクトを返す。ログや例外レポートに秘密情報が混ざらないようにするために使う。

## Signature

```ts
function redact<T>(value: T, keys: readonly string[], mask?: string): T
```

## Usage

```ts
const redact = <T>(value: T, keys: readonly string[] = ['password', 'token', 'authorization', 'secret', 'apiKey', 'cookie'], mask = '[REDACTED]'): T => {
  const lower = new Set(keys.map((k) => k.toLowerCase()));
  const walk = (v: unknown): unknown =>
    Array.isArray(v) ? v.map(walk)
    : v !== null && typeof v === 'object' && Object.getPrototypeOf(v) === Object.prototype
      ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, lower.has(k.toLowerCase()) ? mask : walk(x)])) : v;
  return walk(value) as T;
};
redact({ user: 'a', password: 'p@ss', headers: { Authorization: 'Bearer x' }, items: [{ token: 't' }] });
// => { user: 'a', password: '[REDACTED]', headers: { Authorization: '[REDACTED]' }, items: [{ token: '[REDACTED]' }] }
```

## Contract

- キー名の一致は **大文字小文字を無視** して比較する（`Authorization` / `authorization` / `AUTHORIZATION` はすべて一致）。部分一致はしない（`passwordHash` は `password` に一致しない）
- 一致したキーの値は型を問わず `mask` に置き換える（オブジェクトや配列でも丸ごと）。`null` / `undefined` の値も置き換える
- 純粋関数で、入力を変更しない。プレーンオブジェクト（`Object.prototype` 直下と `Object.create(null)` 由来）と配列は新しいコピーを返し、それ以外（`Date` / `Map` / クラスインスタンス / `Error`）は **中を辿らずそのまま** 返す
- ネストの深さに制限はなく、配列の中のオブジェクト・オブジェクトの中の配列も辿る。循環参照があるとスタックオーバーフローになる
- `keys` が空なら何も置き換えず、構造だけコピーして返す
- 戻り値の型は入力と同じ `T` だが、実際にはマスク位置の値が `string` になっている。型は形の維持を表すだけで値の保証はしない

## Alternatives

- `pino` の `redact: ['password', 'headers.authorization', '*.token']` オプション（パス指定、`fast-redact` ベース）
- `Map` / クラスインスタンスまで辿りたいなら `es-toolkit` の `cloneDeepWith` で変換関数を差し込む
- 値の内容で判定（`Bearer ...` や 16 桁のカード番号）したいなら正規表現で文字列側を置換する。キー名ベースとは別物

## Pitfalls

- キー名は API や環境ごとに違う（`pass` / `pwd` / `x-api-key` / `client_secret` / `refreshToken`）。一覧は用途ごとに見直す
- `Error` や `Request` / `Headers` のようなクラスインスタンスは辿らないので、`headers` は `Object.fromEntries(headers)` などプレーンオブジェクトにしてから渡す
- 文字列の中に埋め込まれた秘密（URL の `?token=...`、`Authorization: Bearer ...` の 1 行）はキー名では見つからない。URL はカード url 系で分解するか、正規表現で別途処理する
- マスク後の値は `string` なので、マスクしたオブジェクトをそのまま処理に使うと型どおりでない値が流れる。ログ直前だけに使う
- `JSON.stringify` の replacer でも同じことはできるが、キーの大文字小文字や配列の扱いを同じにするならこの関数を通してから `stringify` する方が単純

## Test

`examples/log-redact-secrets.test.ts`
