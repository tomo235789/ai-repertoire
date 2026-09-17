PY ?= python3
BASE_URL ?=
# 公開リポジトリ（origin が tomo235789/ai-repertoire）では CI と同じく --public-only を付ける
VALIDATE_FLAGS ?= $(shell git remote get-url origin 2>/dev/null | grep -qE 'tomo235789/ai-repertoire(\.git)?$$' && echo --public-only)

.PHONY: validate build site test test-ts test-py clean

## カードの検証（PR の CI と同じ）
validate:
	$(PY) scripts/validate_cards.py $(VALIDATE_FLAGS)

## reference/ と llms.txt を生成（ローカルプレビュー）
build:
	$(PY) scripts/build_reference.py --base-url "$(BASE_URL)"

## GitHub Pages 用の site/ を組み立てる
site: build
	scripts/build_site.sh

## examples のテストをすべて実行
test: test-ts test-py

test-ts:
	cd typescript && npm test

test-py:
	@if [ -d python/examples ]; then ruff check --config python/lint/ruff.toml python/examples && cd python && pytest -q; else echo "python/examples が無いためスキップ"; fi

clean:
	rm -rf reference llms.txt site _site
