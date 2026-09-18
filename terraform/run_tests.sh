#!/usr/bin/env bash
# terraform/modules/*/ を 1 つずつ init(-backend=false) → validate → tflint → test する。
# 資格情報は不要（tests/*.tftest.hcl は mock_provider を使う）。TFLINT を指定しなければ PATH の tflint。
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
TFLINT="${TFLINT:-tflint}"
export TF_PLUGIN_CACHE_DIR="${TF_PLUGIN_CACHE_DIR:-$HOME/.terraform.d/plugin-cache}"
mkdir -p "$TF_PLUGIN_CACHE_DIR"
"$TFLINT" --init >/dev/null
status=0
for dir in modules/*/; do
  name="$(basename "$dir")"
  (
    cd "$dir"
    terraform init -backend=false -input=false >/dev/null
    terraform validate -no-color >/dev/null
    "$TFLINT" --no-color --config "$ROOT/.tflint.hcl"
    terraform test -no-color
  ) && echo "ok   $name" || { echo "FAIL $name"; status=1; }
done
exit $status
