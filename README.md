# ai-repertoire

AI コーディング向け「引き出し」カタログ。「AI にこう指示すれば再発明せず既存の関数・ライブラリを使ってくれる」ための、用途語で引ける索引を、人間と AI が同じ Markdown で読める形で公開する。

- サイト / llms.txt: `https://tomo235789.github.io/ai-repertoire/`（`llms.txt` は `https://tomo235789.github.io/ai-repertoire/llms.txt`）
- 手本: [Programming-Idioms](https://programming-idioms.org/)（機能 × 言語）、[EffectPatterns](https://github.com/PaulJPhilp/EffectPatterns)（パターン集 + AI 設定同梱）

## 考え方

1. **Markdown が正本**。frontmatter に機械向けメタデータ、本文に人間向け説明。同じファイルを人間と AI が読む
2. **書く単位は言語別**（`typescript/cards/`）、**読む単位は機能別**（`reference/<id>.md`）。後者は CI で生成し Git には含めない
3. 言語横断の結び付けは **カード ID の一致だけ**。同じ機能には言語が違っても同じ ID を付ける

## 使い方

### 人間

- 機能から引く: [reference/index.md](https://tomo235789.github.io/ai-repertoire/reference/index.md)（ID × 言語の対応表）→ `reference/<id>.md`
- 言語から引く: `<lang>/cards/<id>.md`

ローカルで `make build` すると `reference/` と `llms.txt` ができる。

### AI エージェント（Claude Code など）

利用側プロジェクトの `.claude/skills/` に言語ディレクトリを置く（サブモジュールかコピー）。

```
.claude/skills/ts-repertoire/   ← このリポジトリの typescript/ をそのまま
```

CLAUDE.md には次の 1 行だけ書く。

```
ユーティリティ関数を書く前に ts-repertoire Skill を参照する
```

SKILL.md の `description` に「いつ読むか」が書いてあり、必要になった時だけ `cards/` を読む。

### lint

`typescript/lint/eslint.restricted.js` を ESLint の flat config に取り込む。自前実装しがちなパターンに対し、message でカード ID を示す。

## 構成

```
schema/card.schema.json      frontmatter の JSON Schema
scripts/validate_cards.py    PR で走る検証（schema・見出し・ID 整合・Test の存在・status: public）
scripts/build_reference.py   言語別カード → reference/ + index.md + llms.txt
scripts/build_site.sh        GitHub Pages 用 site/ の組み立て
typescript/                  SKILL.md, cards/, examples/（vitest）, lint/
python/                      SKILL.md, cards/, examples/（pytest）, lint/ruff.toml
go/                          SKILL.md, cards/, examples/（go test。samber/lo + stdlib）
csharp/                      SKILL.md, cards/, examples/（xUnit。LINQ + MoreLINQ）
react/                       SKILL.md, cards/（パターン粒度、ID は pattern-*）, examples/（vitest + Testing Library）
cpp/                         SKILL.md, cards/, examples/（g++-14 -std=c++23、std::ranges）
ruby/                        SKILL.md, cards/, examples/（minitest）
rust/                        SKILL.md, cards/, tests/（cargo test、itertools + chrono）
sql/                         SKILL.md, cards/（lib は方言）, examples/（pytest で sqlite と duckdb に実行）
.github/workflows/           validate.yml（PR）, publish.yml（main → Pages）
```

言語ディレクトリはカードができてから作る。空の SKILL.md は置かない。

## カードの書き方

雛形は `typescript/cards/collection-chunk.md`。frontmatter は `schema/card.schema.json` で検証される。

- ファイル名 = `id`。`id` は `<領域>-<動作>[-<修飾>]`（領域: collection / object / string / number / date / function / async / result）。同じ機能には言語が違っても同じ `id` と `title` を付ける
- `##` 見出しは `Signature` `Usage` `Contract` `Alternatives` `Pitfalls` `Test` の順。この 6 つ以外は禁止
- `## Usage` は import 込みで 10 行以内
- `## Contract` には順序保持・入力不変・コールバックの純粋性・空入力の挙動を書く
- `## Test` には `examples/` のパスを書く。CI で実行される
- SQL のカードは `lib` に方言（postgresql / mysql / sqlite / bigquery）、`fn` に構文名を書く
- `verified` は実際に実行して確認した日。未検証なら書かない
- `status` は `public` のみ。それ以外は CI が失敗する

## 開発

```sh
pip install -r scripts/requirements.txt
pip install -r python/requirements.txt   # python/examples のテスト（pytest, ruff, 依存ライブラリ）
make validate      # カード検証
make build         # reference/ と llms.txt を生成
make site          # Pages 用 site/ を組み立て
make test          # examples のテスト（typescript: npm test）
```

## コントリビュート

PR テンプレートのチェックリスト（製品名・社名・業務由来の数値・実データを含まない等）を通してから出す。関数名・契約・境界条件は言語と OSS のものだけで説明できていること。

## ライセンス

- 文章（`*.md`）: [CC BY 4.0](LICENSE-CONTENT)
- コード（`scripts/`、`examples/`、`lint/`、`schema/`）: [MIT](LICENSE)

## 免責

個人プロジェクトであり、所属組織とは無関係。業務上の情報は含まない。無保証。各カードの検証日とライブラリのバージョンは frontmatter の `verified` / `since` を見ること。
