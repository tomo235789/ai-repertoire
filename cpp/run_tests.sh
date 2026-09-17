#!/usr/bin/env bash
# cpp/examples/*_test.cpp を 1 本ずつ C++23 でコンパイルして実行する。
# CXX を指定しなければ g++（macOS では Homebrew の g++-NN と SDKROOT が必要）。
set -euo pipefail
cd "$(dirname "$0")"
CXX="${CXX:-g++}"
if [[ "$(uname)" == "Darwin" && -z "${SDKROOT:-}" ]]; then export SDKROOT="$(xcrun --show-sdk-path)"; fi
mkdir -p build
status=0
for src in examples/*_test.cpp; do
  bin="build/$(basename "${src%.cpp}")"
  if ! "$CXX" -std=c++23 -Wall -Wextra -O1 -pthread -o "$bin" "$src"; then echo "COMPILE FAIL $src"; status=1; continue; fi
  "$bin" || status=1
done
exit $status
