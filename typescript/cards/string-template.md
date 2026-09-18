---
id: string-template
lang: typescript
title: テンプレート文字列に値を埋め込む
tags: [テンプレート, 文字列の埋め込み, 差し込み, プレースホルダー, template, interpolate, placeholder, lodash-template]
lib: es-toolkit/compat
fn: template
since: "1.0.0"
verified: 2026-09-17
status: public
---

lodash 互換の `template` で `<%= %>` / `${}` の差し込み、`<%- %>` の HTML エスケープ、`<% %>` の JS 実行ができる関数を作る。設定ファイルやメール本文など **信頼できるテンプレート** に値を入れるのに使う。

## Signature

```ts
function template(string?: string, options?: TemplateOptions): TemplateExecutor
// TemplateOptions: { escape?: RegExp | null; evaluate?: RegExp | null; interpolate?: RegExp | null; variable?: string; imports?: Record<string, any> }
// TemplateExecutor: ((data?: object) => string) & { source: string }
```

## Usage

```ts
import { template } from 'es-toolkit/compat';

const greet = template('Hello <%= user.name %>! You have ${ count } items.'); // <%= %> と ${} は既定でどちらも使える
greet({ user: { name: 'Ann' }, count: 3 });     // => 'Hello Ann! You have 3 items.'
template('<%- html %>')({ html: '<b>&</b>' });   // => '&lt;b&gt;&amp;&lt;/b&gt;'（HTML エスケープ）
template('<% for (const x of xs) { %><%= x %>,<% } %>')({ xs: [1, 2] }); // => '1,2,'（任意の JS）
template('Hi {{ name }}', { interpolate: /{{([\s\S]+?)}}/g })({ name: 'B' }); // => 'Hi B'（区切りを変える）
```

## Contract

- `template(str)` はテンプレートを **JS 関数にコンパイル**（`new Function`）して返す。返った関数は何度でも呼べ、`source` プロパティに生成されたコードが入る
- 既定の区切りは `<%= expr %>`（そのまま）、`<%- expr %>`（`_.escape` で `& < > " '` をエスケープ）、`<% code %>`（実行）、`${ expr }`（`<%= %>` と同じ）。`interpolate` オプションを指定すると `${}` は無効になり指定した正規表現だけになる
- `data` のプロパティは `with(obj)` で変数として見える。`data` に無い変数を参照すると **実行時に `ReferenceError`**（`a is not defined`）。`variable: 'd'` を指定すると `with` を使わず `d.a` の形で参照する
- 値が `null` / `undefined` なら空文字になる（`[<%= a %>]` → `[]`）
- テンプレート内では `process` などのグローバルにもアクセスできる（`<%= process.env.HOME %>` が動く）。**任意コード実行** なので、ユーザー入力をテンプレートにしてはいけない
- 構文の壊れたテンプレート（`<%= ( %>` など）は `template()` を呼んだ時点で `SyntaxError`

## Alternatives

- 変数の差し込みだけなら JS 標準のテンプレートリテラル `` `Hello ${name}` ``（コンパイル時に解決、任意コード実行の心配がない）
- ユーザーが書いたテンプレートを扱うなら、式を評価しない `mustache` / `handlebars`（ロジックレステンプレート）
- 単純な `{name}` 置換だけなら `str.replace(/\{(\w+)\}/g, (_, k) => data[k] ?? '')`

## Pitfalls

- **信頼できないテンプレートに使わない**。テンプレート文字列がユーザー由来だと任意コード実行になる。`data` 側がユーザー由来なのは問題ない（値として扱われる）
- `<%= %>` はエスケープしない。HTML に埋め込むときは `<%- %>` を使う。逆に `<%- %>` で URL やプレーンテキストを作ると `&#39;` などが混ざる
- `data` に無いキーは空文字にならず `ReferenceError`。省略可能なら `<%= typeof a === 'undefined' ? '' : a %>` か `variable` オプションで `d.a`（`undefined` は空文字になる）
- CSP で `unsafe-eval` を禁止しているブラウザでは `new Function` が使えず動かない
- `import { template } from 'es-toolkit'` には無い。`es-toolkit/compat` から import する

## Test

`examples/string-template.test.ts`
