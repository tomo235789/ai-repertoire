// カード io-glob の Contract を検証するテスト
import { glob, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

let cwd: string;

async function touch(...parts: string[]): Promise<void> {
  const path = join(cwd, ...parts);
  await mkdir(join(path, '..'), { recursive: true });
  await writeFile(path, '');
}

describe('io-glob: glob', () => {
  beforeEach(async () => {
    cwd = await mkdtemp(join(tmpdir(), 'io-glob-'));
    await touch('top.ts');
    await touch('src', 'a.ts');
    await touch('src', 'c.js');
    await touch('src', 'sub', 'b.ts');
    await touch('node_modules', 'pkg', 'index.ts');
  });

  afterEach(async () => {
    await rm(cwd, { recursive: true, force: true });
  });

  it('cwd からの相対パスを / 区切りで yield する（順序は不定なので sort する）', async () => {
    const found = await Array.fromAsync(glob('**/*.ts', { cwd }));
    expect(found.sort()).toEqual(['node_modules/pkg/index.ts', 'src/a.ts', 'src/sub/b.ts', 'top.ts']);
  });

  it('exclude の glob パターンで node_modules を除く', async () => {
    const found = await Array.fromAsync(glob('**/*.ts', { cwd, exclude: ['node_modules/**'] }));
    expect(found.sort()).toEqual(['src/a.ts', 'src/sub/b.ts', 'top.ts']);
  });

  it('exclude の関数はディレクトリで true を返すとその中を辿らない', async () => {
    const asked: string[] = [];
    const found = await Array.fromAsync(
      glob('**/*.ts', {
        cwd,
        exclude: (p) => {
          asked.push(p);
          return p === 'node_modules';
        },
      }),
    );
    expect(found.sort()).toEqual(['src/a.ts', 'src/sub/b.ts', 'top.ts']);
    expect(asked).toContain('node_modules');
    expect(asked.some((p) => p.startsWith('node_modules/'))).toBe(false);
  });

  it('withFileTypes: true で Dirent を yield し、parentPath と name からフルパスを作れる', async () => {
    const found: string[] = [];
    for await (const d of glob('src/**/*.ts', { cwd, withFileTypes: true })) {
      expect(d.isFile()).toBe(true);
      found.push(join(d.parentPath, d.name));
    }
    expect(found.sort()).toEqual([join(cwd, 'src', 'a.ts'), join(cwd, 'src', 'sub', 'b.ts')]);
  });

  it('パターンはディレクトリにもマッチし、配列で複数渡せる', async () => {
    expect((await Array.fromAsync(glob('src/*', { cwd }))).sort()).toEqual(['src/a.ts', 'src/c.js', 'src/sub']);
    const both = await Array.fromAsync(glob(['**/*.ts', '**/*.js'], { cwd, exclude: ['node_modules/**'] }));
    expect(both.sort()).toEqual(['src/a.ts', 'src/c.js', 'src/sub/b.ts', 'top.ts']);
  });

  it('絶対パスのパターンは絶対パスを yield し、マッチ無しは空で例外にならない', async () => {
    expect(await Array.fromAsync(glob(join(cwd, 'src', '*.ts')))).toEqual([join(cwd, 'src', 'a.ts')]);
    expect(await Array.fromAsync(glob('nothing/**', { cwd }))).toEqual([]);
  });
});
