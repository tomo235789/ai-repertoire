// カード io-write-atomic の Contract を検証するテスト
import { randomUUID } from 'node:crypto';
import { mkdir, mkdtemp, readFile, rename, rm, stat, unlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

let dir: string;

async function writeAtomic(target: string, data: string): Promise<void> {
  // 同じプロセス内で同じ対象へ同時に書いても衝突しないよう、呼び出しごとに一意な名前にする
  const tmp = `${target}.${process.pid}.${randomUUID()}.tmp`;
  try {
    await writeFile(tmp, data);
    await rename(tmp, target);
  } catch (err) {
    await unlink(tmp).catch(() => {}); // 失敗しても一時ファイルを残さない
    throw err;
  }
}

describe('io-write-atomic: rename', () => {
  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'io-write-atomic-'));
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  it('既存ファイルを上書きし、一時ファイルは消える', async () => {
    const target = join(dir, 'config.json');
    await writeFile(target, 'old');
    const tmp = join(dir, 'config.json.tmp');
    await writeFile(tmp, 'new');
    await expect(rename(tmp, target)).resolves.toBeUndefined();
    expect(await readFile(target, 'utf8')).toBe('new');
    await expect(stat(tmp)).rejects.toMatchObject({ code: 'ENOENT' });
  });

  it('置き換え後は一時ファイルの inode とパーミッションになる', async () => {
    const target = join(dir, 'secret.txt');
    await writeFile(target, 'old', { mode: 0o600 });
    const tmp = join(dir, 'secret.txt.tmp');
    await writeFile(tmp, 'new', { mode: 0o644 });
    const tmpStat = await stat(tmp);
    await rename(tmp, target);
    const after = await stat(target);
    expect(after.ino).toBe(tmpStat.ino);
    expect(after.mode & 0o777).toBe(0o644);
  });

  it('同時に読んでも途中状態（古い内容と新しい内容の混在）を見ない', async () => {
    const target = join(dir, 'data.txt');
    const a = 'A'.repeat(64 * 1024);
    const b = 'B'.repeat(64 * 1024);
    await writeFile(target, a);
    const writes = (async () => {
      for (let i = 0; i < 50; i++) await writeAtomic(target, i % 2 === 0 ? b : a);
    })();
    const reads = (async () => {
      const seen = new Set<string>();
      for (let i = 0; i < 50; i++) seen.add(await readFile(target, 'utf8'));
      return seen;
    })();
    const [, seen] = await Promise.all([writes, reads]);
    for (const content of seen) expect(content === a || content === b).toBe(true);
  });

  it('rename が失敗しても target は変わらず一時ファイルは残る', async () => {
    const target = join(dir, 'as-dir');
    await mkdir(target); // 置き換え先がディレクトリ
    const tmp = join(dir, 'as-dir.tmp');
    await writeFile(tmp, 'new');
    await expect(rename(tmp, target)).rejects.toMatchObject({ code: 'EISDIR' });
    expect((await stat(target)).isDirectory()).toBe(true);
    expect(await readFile(tmp, 'utf8')).toBe('new');
  });

  it('oldPath や newPath の親ディレクトリが無ければ ENOENT', async () => {
    const target = join(dir, 'x.txt');
    await expect(rename(join(dir, 'missing.tmp'), target)).rejects.toMatchObject({ code: 'ENOENT' });
    await writeFile(target, 'x');
    await expect(rename(target, join(dir, 'no-such-dir', 'x.txt'))).rejects.toMatchObject({ code: 'ENOENT' });
  });
});
