// カード json-stringify-stable の Contract を検証するテスト
import stringify from 'safe-stable-stringify';
import { describe, expect, it } from 'vitest';

describe('json-stringify-stable: stringify', () => {
  it('全階層のキーを昇順に並べ、配列の順序は変えない', () => {
    expect(stringify({ b: 1, a: { d: 2, c: 3 } })).toBe('{"a":{"c":3,"d":2},"b":1}');
    expect(JSON.stringify({ b: 1, a: { d: 2, c: 3 } })).toBe('{"b":1,"a":{"d":2,"c":3}}');
    expect(stringify({ list: [3, 1, 2] })).toBe('{"list":[3,1,2]}');
    expect(stringify({ a: 1, b: 2 })).toBe(stringify({ b: 2, a: 1 }));
  });

  it('循環参照は "[Circular]"、共有参照は展開する', () => {
    const self: Record<string, unknown> = { a: 1 };
    self.self = self;
    expect(stringify(self)).toBe('{"a":1,"self":"[Circular]"}');
    expect(() => JSON.stringify(self)).toThrow(TypeError);
    const shared = { v: 1 };
    expect(stringify({ x: shared, y: shared })).toBe('{"x":{"v":1},"y":{"v":1}}');
  });

  it('bigint は数値リテラルとして出力する', () => {
    expect(stringify({ n: 10n })).toBe('{"n":10}');
    expect(() => JSON.stringify({ n: 10n })).toThrow(TypeError);
    expect(JSON.parse(stringify({ n: 9007199254740993n }) as string)).toEqual({ n: 9007199254740992 });
  });

  it('undefined / 関数 / symbol / NaN / Date / Map / Set は JSON.stringify と同じ扱い', () => {
    const value = { u: undefined, f: () => 1, s: Symbol('s'), nan: Number.NaN, d: new Date(0), m: new Map([[1, 2]]), set: new Set([1]) };
    expect(stringify(value)).toBe('{"d":"1970-01-01T00:00:00.000Z","m":{},"nan":null,"set":{}}');
    expect(stringify([undefined, () => 1, Symbol('s')])).toBe('[null,null,null]');
    expect(stringify(undefined)).toBeUndefined();
    expect(stringify(() => 1)).toBeUndefined();
  });

  it('toJSON の戻り値をソートする', () => {
    expect(stringify({ toJSON: () => ({ z: 1, a: 2 }) })).toBe('{"a":2,"z":1}');
  });

  it('replacer と space は JSON.stringify と同じ意味', () => {
    expect(stringify({ b: 1, a: 2 }, ['a'])).toBe('{"a":2}');
    expect(stringify({ b: 1, a: 2 }, (_key, v: unknown) => (typeof v === 'number' ? v * 10 : v))).toBe('{"a":20,"b":10}');
    expect(stringify({ b: 1, a: 2 }, null, 2)).toBe('{\n  "a": 2,\n  "b": 1\n}');
  });

  it('configure で循環時に例外、ソート無効、bigint 省略にできる', () => {
    const self: Record<string, unknown> = { a: 1 };
    self.self = self;
    expect(() => stringify.configure({ circularValue: Error })(self)).toThrow(TypeError);
    expect(stringify.configure({ deterministic: false })({ b: 1, a: 2 })).toBe('{"b":1,"a":2}');
    expect(stringify.configure({ bigint: false })({ n: 10n })).toBe('{}');
  });

  it('数値風のキーの順序が JSON.stringify と違う', () => {
    const value = { b: 1, 10: 2, 2: 3, a: 4 };
    expect(JSON.stringify(value)).toBe('{"2":3,"10":2,"b":1,"a":4}');
    expect(stringify(value)).toBe('{"10":2,"2":3,"a":4,"b":1}');
  });
});
