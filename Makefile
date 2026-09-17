PY ?= python3
BASE_URL ?=
# 公開リポジトリ（origin が tomo235789/ai-repertoire）では CI と同じく --public-only を付ける
VALIDATE_FLAGS ?= $(shell git remote get-url origin 2>/dev/null | grep -qE 'tomo235789/ai-repertoire(\.git)?$$' && echo --public-only)

.PHONY: validate build site test test-ts test-py test-go test-cs test-react test-cpp test-ruby test-rust test-sql clean

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
test: test-ts test-py test-go test-cs test-react test-cpp test-ruby test-rust test-sql

test-ts:
	cd typescript && npm test

test-py:
	@if [ -d python/examples ]; then ruff check --config python/lint/ruff.toml python/examples && cd python && pytest -q; else echo "python/examples が無いためスキップ"; fi

test-go:
	@if [ -d go/examples ]; then cd go && go vet ./... && go test ./...; else echo "go/examples が無いためスキップ"; fi

test-cs:
	@if [ -d csharp/examples ]; then cd csharp/examples && dotnet test --nologo; else echo "csharp/examples が無いためスキップ"; fi

test-react:
	@if [ -d react/examples ]; then cd react && npm test; else echo "react/examples が無いためスキップ"; fi

test-cpp:
	@if [ -d cpp/examples ]; then cpp/run_tests.sh; else echo "cpp/examples が無いためスキップ"; fi

test-ruby:
	@if [ -d ruby/examples ]; then ruby/run_tests.sh; else echo "ruby/examples が無いためスキップ"; fi

test-rust:
	@if [ -d rust/tests ]; then cd rust && cargo test --quiet; else echo "rust/tests が無いためスキップ"; fi

test-sql:
	@if [ -d sql/examples ]; then cd sql && pytest -q; else echo "sql/examples が無いためスキップ"; fi

clean:
	rm -rf reference llms.txt site _site
