// カード string-slugify の Contract を検証するテスト
import { deburr, kebabCase } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

const slugify = (s: string) => kebabCase(deburr(s));

describe('string-slugify: kebabCase', () => {
  it('Usage のとおりアクセントを除去し、小文字・ハイフン区切りにする', () => {
    expect(slugify('Crème Brûlée à la Mode!')).toBe('creme-brulee-a-la-mode');
    expect(slugify('Hello, World 2024')).toBe('hello-world-2024');
  });

  it('deburr は結合記号を除き、ラテン拡張文字を ASCII に置き換える', () => {
    expect(deburr('Crème brûlée')).toBe('Creme brulee');
    expect(deburr('é')).toBe('e');
    expect(deburr('Ærøskøbing')).toBe('Aeroskobing');
    expect(deburr('Straße')).toBe('Strasse');
    expect(deburr('Łódź')).toBe('Lodz');
  });

  it('連続する区切りや先頭・末尾の記号でハイフンが重ならない', () => {
    expect(slugify('  --Hello,,  World--  ')).toBe('hello-world');
  });

  it('数字は独立した単語になる', () => {
    expect(slugify('Release 2024')).toBe('release-2024');
    expect(slugify('web3 Rock & Roll')).toBe('web-3-rock-roll');
  });

  it('ラテン文字以外は変換も除去もされず残る', () => {
    expect(deburr('日本語')).toBe('日本語');
    expect(slugify('こんにちは 世界')).toBe('こんにちは-世界');
    expect(slugify('日本語のTitle 2024')).toBe('日本語のtitle-2024');
  });

  it('絵文字は 1 単語として残る', () => {
    expect(slugify('hello 🚀 world')).toBe('hello-🚀-world');
  });

  it('空文字や記号のみは空文字を返し、例外を投げない', () => {
    expect(slugify('')).toBe('');
    expect(slugify('!!! ???')).toBe('');
    expect(() => slugify("Don't & Rock")).not.toThrow();
    expect(slugify("Don't stop")).toBe('don-t-stop');
  });

  it('Pitfalls の ASCII 化の前処理で非 ASCII を落とせる', () => {
    const ascii = (s: string) => kebabCase(deburr(s).replace(/[^\x00-\x7F]/g, ' '));
    expect(ascii('Crème こんにちは 世界')).toBe('creme');
    expect(ascii('こんにちは')).toBe('');
  });
  it('単独の絵文字は残り、ZWJ 結合列は要素ごとに分かれる', () => {
    expect(kebabCase(deburr('🐶'))).toBe('🐶');
    expect(kebabCase(deburr('👨‍👩‍👧'))).toBe('👨-👩-👧');
  });
});
