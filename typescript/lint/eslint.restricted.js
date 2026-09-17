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
    // 構文パターンによる検出は AST の形だけを見る発見的ルールなので warn にする。
    // （例: Math.round(x * 1024) / 1024 のような 2 のべき乗量子化や、別の Date へ setDate する処理も一致する）
    // 強制したいプロジェクトは利用側で 'error' に上書きする
    'no-restricted-syntax': [
      'warn',
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
        // indexOf の結果をインデックス変数と等値比較する形に限定し、
        // allowed.indexOf(x) !== -1 のようなメンバーシップ判定や、!== で重複側を抽出する処理は対象外
        selector:
          "CallExpression[callee.property.name='filter'] > :function[params.length=2] BinaryExpression[operator=/^===?$/]" +
          ":matches([left.callee.property.name='indexOf'][right.type='Identifier'], [right.callee.property.name='indexOf'][left.type='Identifier'])",
        message: 'collection-dedup-by-key: 重複除去は es-toolkit の uniq / uniqBy を使う',
      },
      {
        // Math.min(Math.max(x, lo), hi) / Math.max(Math.min(x, hi), lo) による手動クランプ。
        // Math.min(Math.min(a, b), c) のような同種の入れ子（最小値・最大値の計算）は対象外
        selector:
          "CallExpression[callee.object.name='Math'][callee.property.name='min'] > CallExpression[callee.object.name='Math'][callee.property.name='max'], " +
          "CallExpression[callee.object.name='Math'][callee.property.name='max'] > CallExpression[callee.object.name='Math'][callee.property.name='min']",
        message: 'number-clamp: 範囲への丸め込みは es-toolkit の clamp を使う',
      },
      {
        // Math.round(x * 100) / 100 による小数丸め。floor / ceil は切り捨て・切り上げの意図があるので対象外。
        // Number(x.toFixed(n)) は丸め方向が round と異なる場合がある（-1.25 → -1.3 と -1.2）ため対象外
        selector:
          "BinaryExpression[operator='/'] > CallExpression[callee.object.name='Math'][callee.property.name='round'] > BinaryExpression[operator='*']",
        message: 'number-round-to: 桁指定の丸めは es-toolkit の round を使う',
      },
      {
        // new Promise((r) => setTimeout(r, ms)) による手動 sleep
        selector:
          "NewExpression[callee.name='Promise'] > :function[params.length=1] CallExpression[callee.name='setTimeout'][arguments.0.type='Identifier']",
        message: 'async-sleep: 待機は es-toolkit の delay を使う（AbortSignal で中断できる）',
      },
      {
        // d.setDate(d.getDate() + n) による日付の加算（Date を破壊的に変更する）
        selector:
          "CallExpression[callee.property.name='setDate'] > BinaryExpression > CallExpression[callee.property.name='getDate']",
        message: 'date-add-days: 日付の加算は date-fns の addDays を使う（元の Date を変更しない）',
      },
      {
        // Object.fromEntries(Object.entries(o).map/filter(...)) によるオブジェクト変換
        selector:
          "CallExpression[callee.object.name='Object'][callee.property.name='fromEntries'] > CallExpression[callee.property.name=/^(map|filter)$/] > MemberExpression > CallExpression[callee.object.name='Object'][callee.property.name='entries']",
        message: 'object-map-values / object-pick / object-omit: es-toolkit の mapValues / pick / omit / pickBy / omitBy を使う',
      },
    ],
  },
};
