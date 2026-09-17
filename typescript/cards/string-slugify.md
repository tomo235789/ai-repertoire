---
id: string-slugify
lang: typescript
title: 文字列を URL 用のスラッグに変換する
tags: [スラッグ, URL, パーマリンク, アクセント除去, slug, slugify, url, permalink]
lib: es-toolkit
fn: kebabCase
since: "1.0.0"
verified: 2026-09-17
status: public
---

タイトルなどの文字列からアクセントを除き、小文字・ハイフン区切りにして URL パスに使える形にする。`deburr` と `kebabCase` の組み合わせで作る。

## Signature

```ts
function kebabCase(str: string): string
```

## Usage

```ts
import { deburr, kebabCase } from 'es-toolkit';

const slugify = (s: string) => kebabCase(deburr(s));

slugify('Crème Brûlée à la Mode!'); // => 'creme-brulee-a-la-mode'
slugify('Hello, World 2024');      // => 'hello-world-2024'
```

## Contract

- `deburr` は NFD 分解後の結合記号（U+0300–U+036F など）を取り除き、`Æ` → `Ae`、`ß` → `ss`、`Ø` → `O`、`Ł` → `L` などのラテン拡張文字を ASCII に置き換える
- `kebabCase` は空白・記号で単語に分け、小文字化して `-` で連結する。区切りが連続しても `-` は重ならず、先頭・末尾にも付かない
- 数字は独立した単語になる（`2024` はそのまま、`web3` は `web-3`）
- ラテン文字以外（日本語など）は `deburr` で変換されず、`kebabCase` でも単語として残る（`こんにちは 世界` → `こんにちは-世界`）
- 単独の絵文字は 1 単語として残る（`🐶` → `🐶`）。ZWJ で結合した絵文字列（`👨‍👩‍👧`）は要素ごとに分かれて `-` で連結される
- 空文字や記号のみは `''`。例外を投げない。純粋関数

## Alternatives

- lodash 互換の `es-toolkit/compat` の `kebabCase` は内部でアクセント除去とアポストロフィ無視を行うので `deburr` を挟まなくてよい
- 日本語をローマ字化したい場合は翻字ライブラリを別途使う。そのまま URL に入れるなら `encodeURIComponent`
- 長さ制限が必要なら `string-truncate` を後段に足す

## Pitfalls

- 日本語や絵文字は除去されない。ASCII のみにしたければ `deburr` の後に `.replace(/[^\x00-\x7F]/g, ' ')` を挟む（残りが無ければ `''` になる）
- アポストロフィは区切りになる（`Don't` → `don-t`）。lodash / compat は `dont`
- 数字の前後で分割される（`web3` → `web-3`）。製品名などを保ちたいなら自前で分割する
- `&` や `+` は単に消える（`Rock & Roll` → `rock-roll`）。`and` に置き換えたいなら前処理する

## Test

`examples/string-slugify.test.ts`
