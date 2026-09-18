// カード io-temp-dir の Contract を検証するテスト
import { mkdtemp, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { basename, dirname, join, sep } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';

const created: string[] = [];

async function makeTemp(prefix = join(tmpdir(), 'io-temp-dir-')): Promise<string> {
  const dir = await mkdtemp(prefix);
  created.push(dir);
  return dir;
}

describe('io-temp-dir: mkdtemp', () => {
  afterEach(async () => {
    await Promise.all(created.splice(0).map((d) => rm(d, { recursive: true, force: true })));
  });

  it('prefix の直後にランダム 6 文字を付けたディレクトリを作る', async () => {
    const prefix = join(tmpdir(), 'io-temp-dir-');
    const dir = await makeTemp(prefix);
    expect(dir.startsWith(prefix)).toBe(true);
    expect(dir.slice(prefix.length)).toMatch(/^[A-Za-z0-9]{6}$/);
    expect((await stat(dir)).isDirectory()).toBe(true);
  });

  it('区切りは足さないので prefix の末尾がそのまま名前の一部になる', async () => {
    const parent = await makeTemp();
    const dir = await makeTemp(join(parent, 'abc'));
    expect(dirname(dir)).toBe(parent);
    expect(basename(dir)).toMatch(/^abc[A-Za-z0-9]{6}$/);
  });

  it('呼ぶたびに別のディレクトリになる', async () => {
    const dirs = await Promise.all(Array.from({ length: 5 }, () => makeTemp()));
    expect(new Set(dirs).size).toBe(5);
  });

  it('パーミッションは 0700', async () => {
    const dir = await makeTemp();
    expect((await stat(dir)).mode & 0o777).toBe(0o700);
  });

  it('親ディレクトリが無ければ ENOENT', async () => {
    const parent = await makeTemp();
    await expect(mkdtemp(join(parent, 'missing', 'x-'))).rejects.toMatchObject({ code: 'ENOENT' });
  });

  it('rm(recursive, force) で中身ごと消え、無くても失敗しない', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'io-temp-dir-'));
    await writeFile(join(dir, 'file.txt'), 'x');
    await rm(dir, { recursive: true, force: true });
    await expect(stat(dir)).rejects.toMatchObject({ code: 'ENOENT' });
    await expect(rm(dir, { recursive: true, force: true })).resolves.toBeUndefined();
    await expect(rm(dir, { recursive: true })).rejects.toMatchObject({ code: 'ENOENT' });
  });

  it('os.tmpdir() は末尾に区切りを付けない', () => {
    expect(tmpdir().endsWith(sep)).toBe(false);
  });
});
