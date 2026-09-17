// ai-repertoire: 自前実装しがちなパターンを禁止し、カードの関数へ誘導する ESLint ルール集。
// 各 message の先頭にカード ID を書く。カードを追加したら対応ルールをここに足す。
//
// 使い方（flat config）:
//   const repertoire = require('./.claude/skills/ts-repertoire/lint/eslint.restricted.js');
//   module.exports = [ { files: ['**/*.ts'], rules: repertoire.rules } ];

'use strict';

module.exports = {
  rules: {
    'no-restricted-imports': [
      'error',
      {
        paths: [
          { name: 'lodash', message: 'es-toolkit を使う。lodash 互換 API が必要なら es-toolkit/compat' },
          { name: 'lodash-es', message: 'es-toolkit を使う。lodash 互換 API が必要なら es-toolkit/compat' },
          { name: 'underscore', message: 'es-toolkit を使う' },
        ],
        patterns: [{ group: ['lodash/*', 'lodash-es/*', 'lodash.*'], message: 'es-toolkit を使う' }],
      },
    ],
    'no-restricted-syntax': [
      'error',
      {
        // Array.from({ length: Math.ceil(arr.length / size) }, (_, i) => arr.slice(...)) による手動チャンク。
        // コールバックに slice が無い Array.from（単なる個数生成）は対象外
        selector:
          "CallExpression[callee.object.name='Array'][callee.property.name='from']" +
          ":has(ObjectExpression > Property[key.name='length'] > CallExpression[callee.object.name='Math'][callee.property.name='ceil'])" +
          ":has(CallExpression[callee.property.name='slice'])",
        message: 'collection-chunk: 固定長分割は es-toolkit の chunk を使う',
      },
      {
        // arr.filter((x, i) => arr.indexOf(x) === i) による手動重複除去。
        // indexOf の結果をインデックス変数と比較する形に限定し、
        // allowed.indexOf(x) !== -1 のようなメンバーシップ判定は対象外
        selector:
          "CallExpression[callee.property.name='filter'] > :function[params.length=2] BinaryExpression[operator=/^[!=]==?$/]" +
          ":matches([left.callee.property.name='indexOf'][right.type='Identifier'], [right.callee.property.name='indexOf'][left.type='Identifier'])",
        message: 'collection-dedup-by-key: 重複除去は es-toolkit の uniq / uniqBy を使う',
      },
    ],
  },
};
