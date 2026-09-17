// カード pattern-list-keys の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EditableRows, type Row } from './pattern-list-keys';

const rows: Row[] = [
  { id: 'a', label: 'a' },
  { id: 'b', label: 'b' },
  { id: 'c', label: 'c' },
];

const valueOf = (label: string) => screen.getByLabelText<HTMLInputElement>(label).value;

describe('pattern-list-keys', () => {
  afterEach(cleanup);

  it('id を key にすると、並べ替えても入力の状態は同じ行に付いていく', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<EditableRows rows={rows} keyBy="id" />);
    await user.type(screen.getByLabelText('a'), 'hello');
    rerender(<EditableRows rows={[...rows].reverse()} keyBy="id" />);
    expect(screen.getAllByRole('listitem').map((li) => li.textContent)).toEqual(['c', 'b', 'a']);
    expect(valueOf('a')).toBe('hello');
    expect(valueOf('c')).toBe('');
  });

  it('index を key にすると、並べ替えで入力の状態が別の行に付く', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<EditableRows rows={rows} keyBy="index" />);
    await user.type(screen.getByLabelText('a'), 'hello');
    rerender(<EditableRows rows={[...rows].reverse()} keyBy="index" />);
    expect(valueOf('c')).toBe('hello'); // 位置 0 の DOM がそのまま使い回され、ラベルだけ c になる
    expect(valueOf('a')).toBe('');
  });

  it('id を key にすると、先頭を削除しても残りの行の状態は保たれ、削除した行だけがアンマウントされる', async () => {
    const user = userEvent.setup();
    const mountLog: string[] = [];
    const { rerender } = render(<EditableRows rows={rows} keyBy="id" mountLog={mountLog} />);
    await user.type(screen.getByLabelText('b'), 'keep');
    rerender(<EditableRows rows={rows.slice(1)} keyBy="id" mountLog={mountLog} />);
    expect(valueOf('b')).toBe('keep');
    expect(mountLog).toEqual(['mount:a', 'mount:b', 'mount:c', 'unmount:a']);
  });

  it('index を key にすると、先頭を削除したときに末尾がアンマウントされ、入力の状態が 1 つずつずれる', async () => {
    const user = userEvent.setup();
    const mountLog: string[] = [];
    const { rerender } = render(<EditableRows rows={rows} keyBy="index" mountLog={mountLog} />);
    await user.type(screen.getByLabelText('a'), 'typed');
    rerender(<EditableRows rows={rows.slice(1)} keyBy="index" mountLog={mountLog} />);
    expect(valueOf('b')).toBe('typed'); // a に入力した値が b に付く
    expect(mountLog).toEqual(['mount:a', 'mount:b', 'mount:c', 'unmount:c']);
  });

  it('key を変えると同じ位置でも別の要素として作り直され、状態がリセットされる', async () => {
    const user = userEvent.setup();
    function Editor({ userId }: { userId: string }) {
      const [text, setText] = useState('');
      return <input aria-label={`memo-${userId}`} value={text} onChange={(e) => setText(e.target.value)} />;
    }
    function Page() {
      const [userId, setUserId] = useState('u1');
      return (
        <>
          <button onClick={() => setUserId('u2')}>switch</button>
          <Editor key={userId} userId={userId} />
        </>
      );
    }
    render(<Page />);
    await user.type(screen.getByLabelText('memo-u1'), 'draft');
    await user.click(screen.getByText('switch'));
    expect(screen.getByLabelText('memo-u2')).toHaveValue('');
  });

  it('key が重複すると React が警告する', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(<EditableRows rows={[rows[0], { ...rows[1], id: 'a' }]} keyBy="id" />);
    expect(errorSpy.mock.calls[0][0]).toContain('Encountered two children with the same key');
    errorSpy.mockRestore();
  });
});
