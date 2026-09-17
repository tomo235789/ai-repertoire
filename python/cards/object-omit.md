---
id: object-omit
lang: python
title: オブジェクトから指定したキーを除いたコピーを作る
tags: [除外, キー削除, 部分辞書, omit, exclude-keys, drop-keys, without]
lib: stdlib
fn: dict comprehension
since: "3.7"
verified: 2026-09-17
preserves_order: true
status: public
---

辞書から不要なキーを除いた新しい辞書を作る。パスワードなど外に出したくないフィールドの除去に使う。

## Signature

```python
{k: v for k, v in d.items() if k not in excluded}
```

## Usage

```python
user = {"id": 1, "name": "a", "password": "x"}
excluded = {"password", "token"}
{k: v for k, v in user.items() if k not in excluded}
# => {'id': 1, 'name': 'a'}
```

## Contract

- 入力辞書を変更しない。返り値は新しい `dict`（値は浅いコピー。ネストした辞書やリストは同じ参照）
- 残ったキーの順序は元の辞書のまま
- 存在しないキーを `excluded` に入れても無視される
- すべてのキーを除くと `{}`。`excluded` が空なら元と同じ内容の別オブジェクト
- 例外は投げない

## Alternatives

- 元の辞書を破壊的に変えてよいなら `d.pop("password", None)`（存在しなくても失敗しない。`del d["password"]` は存在しないと `KeyError`）
- 値の条件で除くなら `{k: v for k, v in d.items() if v is not None}`
- 残す側を列挙するなら object-pick

## Pitfalls

- `excluded` はリストでも動くが、`in` が線形探索になる。除外キーが多いときは `set` にする（結果は同じ）
- TypeScript 版（es-toolkit の `omit`）と同じ意味論。`del d[k]` や `d.pop(k)` は元の辞書を変えるので違う
- `dict` のキーは挿入順なので、`excluded` を `set` にしても返り値の順序には影響しない

## Test

`examples/object-omit_test.py`
