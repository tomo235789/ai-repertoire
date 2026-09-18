// カード error-assert-never の Contract を検証するテスト
// 網羅漏れの検出は tsc --noEmit で行う。@ts-expect-error の行は「型エラーがある」ことを tsc が確認する
import { describe, expect, it } from 'vitest';

function assertNever(value: never, message = `Unexpected value: ${JSON.stringify(value)}`): never {
  throw new Error(message);
}

type Shape = { kind: 'circle'; r: number } | { kind: 'square'; s: number } | { kind: 'triangle'; b: number; h: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.r ** 2;
    case 'square':
      return shape.s ** 2;
    case 'triangle':
      return (shape.b * shape.h) / 2;
    default:
      return assertNever(shape); // 全ケース処理済みなので shape は never
  }
}

function areaMissingTriangle(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.r ** 2;
    case 'square':
      return shape.s ** 2;
    default:
      // @ts-expect-error 'triangle' が未処理なので shape は never に代入できない
      return assertNever(shape);
  }
}

describe('error-assert-never: never 型', () => {
  it('全ケースを処理していれば default は never に絞り込まれ、通常どおり動く', () => {
    expect(area({ kind: 'square', s: 3 })).toBe(9);
    expect(area({ kind: 'triangle', b: 4, h: 5 })).toBe(10);
  });

  it('網羅漏れは tsc が検出する（@ts-expect-error が消えると tsc が失敗する）。実行時には throw する', () => {
    expect(() => areaMissingTriangle({ kind: 'triangle', b: 1, h: 1 })).toThrow('Unexpected value: {"kind":"triangle","b":1,"h":1}');
  });

  it('型を通らない値（キャストや JSON）が届いたら Error を投げる', () => {
    const fromJson = JSON.parse('{"kind":"hexagon"}') as Shape;
    expect(() => area(fromJson)).toThrow(/Unexpected value: {"kind":"hexagon"}/);
    expect(() => assertNever('x' as never, 'custom')).toThrow(new Error('custom'));
  });

  it('const _: never = x の代入だけでも検出でき、実行時には何もしない', () => {
    const check = (shape: Shape): string => {
      if (shape.kind === 'circle') return 'c';
      if (shape.kind === 'square') return 's';
      if (shape.kind === 'triangle') return 't';
      const _exhaustive: never = shape;
      return _exhaustive;
    };
    expect(check({ kind: 'circle', r: 1 })).toBe('c');
  });

  it('string のような開いた型は絞り込んでも never にならない', () => {
    const f = (s: string) => {
      if (s === 'a') return 1;
      // @ts-expect-error s は string のままで never に代入できない
      return assertNever(s);
    };
    expect(f('a')).toBe(1);
  });

  it('JSON.stringify できない値でメッセージを組むと TypeError になるので注意', () => {
    expect(() => assertNever(1n as never)).toThrow(TypeError);
  });
});
