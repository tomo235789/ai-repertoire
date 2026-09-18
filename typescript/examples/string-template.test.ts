// カード string-template の Contract を検証するテスト
import { template } from 'es-toolkit/compat';
import { describe, expect, it } from 'vitest';

describe('string-template: template', () => {
  it('<%= %> と ${} で値を差し込み、返った関数は何度でも呼べる', () => {
    const greet = template('Hello <%= user.name %>! You have ${ count } items.');
    expect(greet({ user: { name: 'Ann' }, count: 3 })).toBe('Hello Ann! You have 3 items.');
    expect(greet({ user: { name: 'Bob' }, count: 0 })).toBe('Hello Bob! You have 0 items.');
    expect(greet.source).toContain('function(obj)');
  });

  it('<%- %> は HTML エスケープし、<%= %> はしない', () => {
    expect(template('<%- html %>')({ html: '<b>&"\'</b>' })).toBe('&lt;b&gt;&amp;&quot;&#39;&lt;/b&gt;');
    expect(template('<%= html %>')({ html: '<b>' })).toBe('<b>');
  });

  it('<% %> で任意の JS を実行できる', () => {
    expect(template('<% for (const x of xs) { %><%= x %>,<% } %>')({ xs: [1, 2, 3] })).toBe('1,2,3,');
    expect(template('<% if (ok) { %>yes<% } else { %>no<% } %>')({ ok: false })).toBe('no');
  });

  it('interpolate オプションで区切りを変えると ${} は無効になる', () => {
    const mustache = template('Hi {{ name }} ${ name }', { interpolate: /{{([\s\S]+?)}}/g });
    expect(mustache({ name: 'B' })).toBe('Hi B ${ name }');
  });

  it('data に無い変数は ReferenceError。variable オプションなら undefined 扱いで空文字', () => {
    expect(() => template('<%= missing %>')({})).toThrow(ReferenceError);
    expect(template('[<%= d.missing %>]', { variable: 'd' })({})).toBe('[]');
    expect(template('<%= d.a %>', { variable: 'd' })({ a: 9 })).toBe('9');
  });

  it('null / undefined の値は空文字になる', () => {
    expect(template('[<%= a %>]')({ a: null })).toBe('[]');
    expect(template('[<%= a %>]')({ a: undefined })).toBe('[]');
    expect(template('plain')()).toBe('plain');
  });

  it('テンプレートからグローバルに触れる（任意コード実行）ので信頼できないテンプレートに使わない', () => {
    expect(template('<%= typeof process.pid %>')({})).toBe('number');
    // data 側がユーザー由来でも値として扱われるだけで実行はされない
    expect(template('<%= input %>')({ input: '<%= process.pid %>' })).toBe('<%= process.pid %>');
  });

  it('壊れたテンプレートはコンパイル時に SyntaxError', () => {
    expect(() => template('<%= ( %>')).toThrow(SyntaxError);
  });

  it('imports で _ を差し替え・追加でき、既定で _.escape が使える', () => {
    expect(template('<%= _.escape(a) %>')({ a: '<x>' })).toBe('&lt;x&gt;');
    expect(template('<%= upper(a) %>', { imports: { upper: (s: string) => s.toUpperCase() } })({ a: 'x' })).toBe('X');
  });
});
