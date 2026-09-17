---
id: string-slugify
lang: python
title: 文字列を URL 用のスラッグに変換する
tags: [スラッグ, URL, パーマリンク, アクセント除去, slug, slugify, url, permalink]
lib: python-slugify
fn: slugify
since: "8.0"
verified: 2026-09-17
status: public
---

タイトルなどの文字列からアクセントを除き、小文字・ハイフン区切りの ASCII にして URL パスに使える形にする。

## Signature

```python
slugify.slugify(text, entities=True, decimal=True, hexadecimal=True, max_length=0, word_boundary=False, separator='-', save_order=False, stopwords=(), regex_pattern=None, lowercase=True, replacements=(), allow_unicode=False)
```

## Usage

```python
from slugify import slugify

slugify("Crème Brûlée à la Mode!")                       # => 'creme-brulee-a-la-mode'
slugify("Hello, World 2024")                             # => 'hello-world-2024'
slugify("Hello World Foo Bar", max_length=8)             # => 'hello-wo'
slugify("Hello World Foo Bar", max_length=8, word_boundary=True)  # => 'hello'
slugify("Hello World", separator="_")                    # => 'hello_world'
```

## Contract

- `allow_unicode=False`（既定）なら結果は `[a-z0-9]` と `separator` のみ（`allow_unicode=True` では非 ASCII が残る）。空白・記号は区切りになり、連続しても `separator` は重ならず、先頭・末尾にも付かない（`"a--b__c"` → `'a-b-c'`）
- ラテン拡張文字は ASCII に転写する（`Æ` → `ae`、`ß` → `ss`、`Ø` → `o`、`Ł` → `l`）。日本語・中国語も **除去ではなく転写** される（`"こんにちは 世界"` → `'konnitiha-shi-jie'`、`"北京"` → `'bei-jing'`）。転写は `Unidecode` がインストール済みならそれを優先し、無ければ text-unidecode を使うため、非 ASCII 入力の結果は環境で変わり得る（上の例は text-unidecode）
- 絵文字は除去される（`"hello 🐶 world"` → `'hello-world'`）。HTML エンティティ（`&amp;`、`&#169;`）はデコードしてから処理する
- 数字は前後の文字と分割されない（`web3` → `web3`）。`½` は `1-2`
- `max_length` を超える分は末尾から切る（`word_boundary=False` なら単語の途中でも切る）。切った後に末尾が `separator` になれば落とす。`word_boundary=True` なら完全な単語だけ残す
- `allow_unicode=True` なら非 ASCII を転写せずに残す（`"Crème"` → `'crème'`）。`lowercase=False` なら大文字を保つ
- 空文字・記号のみは `''`。`str` / `bytes` / `bytearray` 以外は `TypeError`（`None`、`int`）
- 純粋関数

## Alternatives

- `replacements=[["&", "and"]]` で転写の前に文字列置換できる（`"Rock & Roll"` → `'rock-and-roll'`）
- 依存を増やせない場合は `unicodedata.normalize("NFKD", s).encode("ascii", "ignore")` で結合記号を落としてから `re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")`（`ß`・`Æ`・日本語は転写されずに消える）
- 転写せずに日本語を URL に入れるなら `urllib.parse.quote`

## Pitfalls

- TypeScript（es-toolkit の `kebabCase(deburr())`）は日本語を単語として残す（`こんにちは-世界`）が、`slugify` はローマ字風に転写する。同じ入力から言語間で別のスラッグが出るので、既存の URL と揃えるなら片方に寄せる
- es-toolkit は camelCase の大文字境界や数字の前後で分割する（`userProfileURL` → `user-profile-url`、`web3` → `web-3`）が、`slugify` は分割しない（`'userprofileurl'`、`'web3'`）
- `&` は単に消える（`"Rock & Roll"` → `'rock-roll'`）。`and` にしたいなら `replacements`
- アポストロフィは区切りになる（`"Don't"` → `'don-t'`）。TypeScript 版と同じ
- `max_length` 既定の `0` は無制限。単語の途中で切りたくなければ `word_boundary=True` を必ず併用する

## Test

`examples/string-slugify_test.py`
