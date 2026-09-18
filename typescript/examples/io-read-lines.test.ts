// カード io-read-lines の Contract を検証するテスト
import { createReadStream } from 'node:fs';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { Readable } from 'node:stream';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

let dir: string;

async function linesOf(text: string): Promise<string[]> {
  const path = join(dir, 'input.txt');
  await writeFile(path, text);
  const rl = createInterface({ input: createReadStream(path), crlfDelay: Infinity });
  const lines: string[] = [];
  for await (const line of rl) lines.push(line);
  return lines;
}

describe('io-read-lines: createInterface', () => {
  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'io-read-lines-'));
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  it('LF / CRLF / 単独 CR のどれも行区切りになり、改行文字は含まれない', async () => {
    expect(await linesOf('a\nb\nc\n')).toEqual(['a', 'b', 'c']);
    expect(await linesOf('a\r\nb\r\nc\r\n')).toEqual(['a', 'b', 'c']);
    expect(await linesOf('a\rb\rc')).toEqual(['a', 'b', 'c']);
  });

  it('末尾の改行 1 つは最後の空行にならない', async () => {
    expect(await linesOf('a\nb')).toEqual(['a', 'b']);
    expect(await linesOf('a\nb\n')).toEqual(['a', 'b']);
    expect(await linesOf('a\n\n')).toEqual(['a', '']);
    expect(await linesOf('a\n\nb\n')).toEqual(['a', '', 'b']);
    expect(await linesOf('')).toEqual([]);
    expect(await linesOf('\n')).toEqual(['']);
  });

  it('split("\\n") は末尾に空文字列が増え、\\r も残る', async () => {
    expect('a\nb\n'.split('\n')).toEqual(['a', 'b', '']);
    expect('a\r\nb\r\n'.split('\n')).toEqual(['a\r', 'b\r', '']);
  });

  it('crlfDelay: Infinity なら \\r と \\n が別チャンクで届いても 1 つの改行になる', async () => {
    const collect = async (crlfDelay: number | undefined) => {
      const input = new Readable({ read() {} });
      const rl = createInterface({ input, crlfDelay });
      const lines: string[] = [];
      const done = (async () => {
        for await (const line of rl) lines.push(line);
      })();
      input.push('a\r');
      await new Promise((r) => setTimeout(r, 150)); // 既定の 100ms を超えて待つ
      input.push('\nb\n');
      input.push(null);
      await done;
      return lines;
    };
    expect(await collect(Infinity)).toEqual(['a', 'b']);
    expect(await collect(undefined)).toEqual(['a', '', 'b']);
  });

  it('break しても close は出ず、入力ストリームは自分で破棄する', async () => {
    const path = join(dir, 'many.txt');
    await writeFile(path, Array.from({ length: 100 }, (_, i) => `line ${i}`).join('\n'));
    const stream = createReadStream(path);
    const rl = createInterface({ input: stream, crlfDelay: Infinity });
    let closeFired = false;
    rl.on('close', () => {
      closeFired = true;
    });
    const seen: string[] = [];
    try {
      for await (const line of rl) {
        seen.push(line);
        if (seen.length === 3) break;
      }
    } finally {
      rl.close(); // break だけでは 'close' は出ない
      stream.destroy(); // rl.close() はストリームを破棄しないので自分で閉じる
    }
    expect(seen).toEqual(['line 0', 'line 1', 'line 2']);
    await new Promise((resolve) => setImmediate(resolve));
    expect(closeFired).toBe(true); // rl.close() を呼んだので出る（break だけでは出ない）
    expect(stream.destroyed).toBe(true);
  });

  it('存在しないファイルは for await の例外になる', async () => {
    const rl = createInterface({ input: createReadStream(join(dir, 'missing.txt')), crlfDelay: Infinity });
    const read = async () => {
      for await (const _line of rl) {
        // 何も読めない
      }
    };
    await expect(read()).rejects.toMatchObject({ code: 'ENOENT' });
  });
});
