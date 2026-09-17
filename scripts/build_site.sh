#!/usr/bin/env bash
# GitHub Pages 用の site/ を組み立てる。build_reference.py を先に実行しておくこと。
# Makefile（ローカルプレビュー）と .github/workflows/publish.yml の両方から呼ぶ。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE="${1:-$ROOT/site}"

# 誤削除防止: 既存の SITE は空か、このスクリプトが書いた _config.yml があるときだけ消す
if [ -d "$SITE" ] && [ -n "$(ls -A "$SITE")" ] && ! grep -q '^title: ai-repertoire$' "$SITE/_config.yml" 2>/dev/null; then
  echo "中止: $SITE は build_site.sh の生成物ではないので削除しない" >&2
  exit 1
fi
rm -rf "$SITE"
mkdir -p "$SITE"
cp "$ROOT/README.md" "$ROOT/llms.txt" "$ROOT/LICENSE" "$ROOT/LICENSE-CONTENT" "$SITE/"
[ -d "$ROOT/docs" ] && cp -r "$ROOT/docs" "$SITE/docs"
cp -r "$ROOT/reference" "$SITE/reference"

for lang in typescript python go csharp cpp react ruby rust sql; do
  if [ -d "$ROOT/$lang/cards" ]; then
    mkdir -p "$SITE/$lang"
    cp -r "$ROOT/$lang/cards" "$SITE/$lang/cards"
    [ -f "$ROOT/$lang/SKILL.md" ] && cp "$ROOT/$lang/SKILL.md" "$SITE/$lang/"
  fi
done

# Jekyll（github-pages gem）の設定。frontmatter の無い .md も HTML 化し、元の .md も残す（llms.txt から参照するため）
cat > "$SITE/_config.yml" <<'YAML'
title: ai-repertoire
theme: jekyll-theme-primer
markdown: kramdown
optional_front_matter:
  remove_originals: false
include:
  - llms.txt
YAML

echo "site: $SITE"
find "$SITE" -type f | sort
