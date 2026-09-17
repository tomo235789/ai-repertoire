---
id: pattern-controlled-input
lang: react
title: 入力を value と onChange で state に持つ
tags: [フォーム, 入力, 制御, 非制御, controlled-input, useState, onChange, defaultValue]
lib: react
fn: useState
since: "18.0"
verified: 2026-09-17
status: public
---

入力中の値を使って送信ボタンの活性・バリデーション・正規化をしたいとき。`value` と `onChange` を対で渡し、React の state を唯一の情報源にする。

## Signature

```tsx
function NameForm(props: { onSubmit: (name: string) => void }): JSX.Element
<input value={string} onChange={(e: ChangeEvent<HTMLInputElement>) => void} />
```

## Usage

```tsx
import { useState } from 'react';
function NameForm({ onSubmit }: { onSubmit: (name: string) => void }) {
  const [name, setName] = useState('');
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(name.trim()); }}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <button type="submit" disabled={name.trim() === ''}>送信</button>
    </form>
  ); // => 入力のたびに state が更新され、ボタンの活性は state から導出される
}
```

## Contract

- 入力するたびに `onChange` で state が更新され、DOM の `value` は state と一致する。送信時は state の値（trim 済み）が渡る
- state を変えれば DOM の値も変わる（「クリア」で `''` にすれば入力欄も空になる）。DOM ではなく state が唯一の情報源
- `onChange` で正規化した値（大文字化など）を state に入れると、表示もその値になる
- `value` だけ渡して `onChange` を省くと React が警告し、入力しても値は変わらない（読み取り専用になる）
- 非制御（`defaultValue` + `ref`）は入力中に再レンダーせず、送信時に `ref.current.value` から読む

## Alternatives

- 入力中の値を使わない（送信時にだけ読む）単純なフォームは非制御にして再レンダーを避ける。React 19 なら `<form action={fn}>` と `FormData` で `ref` も不要
- 項目が多い・バリデーションが複雑なら React Hook Form（非制御ベース）などのライブラリ
- 読み取り専用で表示したいだけなら `readOnly` を付ける（警告が出ない）

## Pitfalls

- `value={undefined}` から文字列に変わると「非制御から制御に切り替わった」警告が出る。初期値は `''` にする
- `value={name}` と `onChange` の間に非同期（デバウンスした `setState`）を挟むと入力が巻き戻る。表示用 state は同期で更新し、デバウンスは送信・検索側にかける
- `<input type="number">` の `value` も文字列として扱う。`Number()` に変換するのは送信時か導出時
- `e.target.value` を非同期に読まない。React 17 以降イベントプーリングは無いが、コールバック内で同期的に取り出す方が安全

## Test

`examples/pattern-controlled-input.test.tsx`
