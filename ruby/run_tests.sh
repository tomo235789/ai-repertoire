#!/usr/bin/env bash
# ruby/examples/*_test.rb を minitest で実行する（Ruby 3.4 以上）。
set -euo pipefail
cd "$(dirname "$0")"
exec ruby -Iexamples -e 'Dir["examples/*_test.rb"].sort.each { |f| require File.expand_path(f) }'
