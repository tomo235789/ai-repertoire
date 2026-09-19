# ai-repertoire（非公開・下書き側）

AI コーディング向け「引き出し」カタログ。「AI にこう指示すれば再発明せず既存の関数・ライブラリを使ってくれる」ための、用途語で引ける索引を、人間と AI が同じ Markdown で読める形にする。

- 手本: [Programming-Idioms](https://programming-idioms.org/)（機能 × 言語）、[EffectPatterns](https://github.com/PaulJPhilp/EffectPatterns)（パターン集 + AI 設定同梱）
- 計画: [docs/ai_repertoire_catalog_plan.md](docs/ai_repertoire_catalog_plan.md)
- 進捗まとめ: [docs/status_2026-09-17.md](docs/status_2026-09-17.md)（Phase 5 まで完了、Phase 6 は作業中ブランチで停止）
- 公開側: `tomo235789/ai-repertoire`（`status: public` のカードだけを書き直して置く。§公開運用）
- GitHub Pages / llms.txt: `https://tomo235789.github.io/ai-repertoire/`（公開側の main から配信中。`llms.txt` は `/llms.txt`）

## 考え方

1. **Markdown が正本**。frontmatter に機械向けメタデータ、本文に人間向け説明
2. **書く単位は言語別**（`typescript/cards/`）、**読む単位は機能別**（`reference/<id>.md`）。後者は CI で生成し Git には含めない
3. 言語横断の結び付けは **カード ID の一致だけ**。同じ機能には言語が違っても同じ ID を付ける

## 使い方

### 人間

- 機能から引く: 生成された `reference/index.md`（ID × 言語の対応表）→ `reference/<id>.md`
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
scripts/validate_cards.py    PR で走る検証（schema・見出し・ID 整合・Test の存在）
scripts/build_reference.py   言語別カード → reference/ + index.md + llms.txt
scripts/build_site.sh        GitHub Pages 用 site/ の組み立て
typescript/                  SKILL.md, cards/, examples/（vitest）, lint/
python/                      SKILL.md, cards/, examples/（pytest）, lint/ruff.toml
go/                          SKILL.md, cards/, examples/（go test。samber/lo + stdlib）
csharp/                      SKILL.md, cards/, examples/（xUnit。LINQ + MoreLINQ）
react/                       SKILL.md, cards/（パターン粒度、ID は pattern-*）, examples/（vitest + Testing Library）
cpp/                         SKILL.md, cards/, examples/（g++ -std=c++23、std::ranges）
ruby/                        SKILL.md, cards/, examples/（minitest）
rust/                        SKILL.md, cards/, tests/（cargo test、itertools + chrono）
sql/                         SKILL.md, cards/（lib は方言）, examples/（pytest で sqlite と duckdb に実行）
terraform/                   SKILL.md, cards/, modules/<id>/（provider を持たない純粋な module + tftest）
aws/                         SKILL.md, cards/, examples/（「要求 → 設定」の純粋関数。pytest）
gcp/                         SKILL.md, cards/, examples/（「要求 → 設定」の純粋関数。pytest）
azure/                       SKILL.md, cards/, examples/（「要求 → 設定」の純粋関数。pytest）
docs/                        計画書
.github/workflows/           validate.yml（PR）, publish.yml（main → Pages。公開リポジトリでのみ動く）
```

言語ディレクトリはカードができてから作る。空の SKILL.md は置かない。

## カードの書き方

仕様は [計画書 §3](docs/ai_repertoire_catalog_plan.md#3-カード仕様)。要点:

- ファイル名 = `id`。`id` は `<領域>-<動作>[-<修飾>]`（領域: collection / object / string / number / date / function / async / result）
- `##` 見出しは `Signature` `Usage` `Contract` `Alternatives` `Pitfalls` `Test` の順。この 6 つ以外は禁止
- `## Usage` は import 込みで 10 行以内
- `## Test` には `examples/` のパスを書く。CI で実行される
- SQL のカードは `lib` に方言（postgresql / mysql / sqlite / bigquery）、`fn` に構文名を書く
- クラウド（terraform / aws / gcp / azure）のカードは「業務上の要求」を入力、「SDK やテンプレートに渡す設定」を出力とする純粋関数にする。API 呼び出し・認証・現在時刻・乱数は関数の外に出す
- `verified` は実際に実行して確認した日。未検証なら書かない
- examples が Python の言語（python / sql / aws / gcp / azure）は、`## Signature` の引数と `## Usage` の呼び出しが実装と一致しているか CI が検査する

雛形は `typescript/cards/collection-chunk.md`。

## 開発

```sh
pip install -r scripts/requirements.txt
pip install -r python/requirements.txt   # python/examples のテスト（pytest, ruff, 依存ライブラリ）
make validate      # カード検証
make build         # reference/ と llms.txt を生成
make site          # Pages 用 site/ を組み立て
make test          # examples のテスト（typescript: npm test）
```

## 公開運用

| リポジトリ | 内容 |
|---|---|
| `ai-repertoire-private`（ここ） | 業務で得た具体例を含む下書き。`status: draft` / `private` / `public` |
| `ai-repertoire`（公開） | `status: public` のみ。CI が `--public-only` で検証し、それ以外を検出したら失敗。Pages への配信（`publish.yml`）もこのリポジトリでしか動かない |

移送はコピーではなく **公開側で書き直す**。書き直し時に [計画書 §8.2 の抽象化チェックリスト](docs/ai_repertoire_catalog_plan.md#82-抽象化チェックリスト公開-pr-テンプレートに入れる) を通す。

## ライセンス

- 文章（`*.md`）: [CC BY 4.0](LICENSE-CONTENT)
- コード（`scripts/`、`examples/`、`lint/`、`schema/`）: [MIT](LICENSE)

## 免責

個人プロジェクトであり、所属組織とは無関係。業務上の情報は含まない。無保証。各カードの検証日とライブラリのバージョンは frontmatter の `verified` / `since` を見ること。
