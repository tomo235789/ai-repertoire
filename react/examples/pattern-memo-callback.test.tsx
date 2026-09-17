// カード pattern-memo-callback の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { IncrementButton, Row, Toolbar } from './pattern-memo-callback';

/** 比較用: 毎回インライン関数を渡す親 */
function ToolbarInline({ childRenders }: { childRenders: number[] }) {
  const [count, setCount] = useState(0);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  return (
    <div>
      <p>count: {count}</p>
      <button onClick={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}>theme: {theme}</button>
      <IncrementButton onClick={() => setCount((c) => c + 1)} renders={childRenders} />
    </div>
  );
}

describe('pattern-memo-callback', () => {
  afterEach(cleanup);

  it('useCallback で安定させたコールバックを渡すと、親の無関係な更新で memo 化した子は再レンダーされない', async () => {
    const user = userEvent.setup();
    const childRenders: number[] = [];
    render(<Toolbar childRenders={childRenders} />);
    expect(childRenders).toHaveLength(1);

    await user.click(screen.getByText('theme: light'));
    await user.click(screen.getByText('theme: dark'));
    expect(screen.getByText('theme: light')).toBeInTheDocument(); // 親は再レンダーされている
    expect(childRenders).toHaveLength(1); // 子は初回のまま
  });

  it('依存配列が空でも関数型更新なら最新の state を正しく更新できる', async () => {
    const user = userEvent.setup();
    const childRenders: number[] = [];
    render(<Toolbar childRenders={childRenders} />);
    await user.click(screen.getByText('+1'));
    await user.click(screen.getByText('+1'));
    expect(screen.getByText('count: 2')).toBeInTheDocument();
    expect(childRenders).toHaveLength(1); // count は子に渡していないので再レンダーされない
  });

  it('インライン関数を渡すと毎回別の関数になり、memo 化していても子は毎回再レンダーされる', async () => {
    const user = userEvent.setup();
    const childRenders: number[] = [];
    render(<ToolbarInline childRenders={childRenders} />);
    await user.click(screen.getByText('theme: light'));
    await user.click(screen.getByText('theme: dark'));
    expect(childRenders).toHaveLength(3);
  });

  it('依存する値が変わったときだけ新しい関数になり、子も再レンダーされる', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const childRenders: number[] = [];
    const { rerender } = render(<Row id={1} label="a" onSelect={onSelect} childRenders={childRenders} />);
    rerender(<Row id={1} label="b" onSelect={onSelect} childRenders={childRenders} />);
    expect(screen.getByText('b')).toBeInTheDocument();
    expect(childRenders).toHaveLength(1); // label は依存に無いので子は再レンダーされない

    rerender(<Row id={2} label="b" onSelect={onSelect} childRenders={childRenders} />);
    expect(childRenders).toHaveLength(2);
    await user.click(screen.getByText('select'));
    expect(onSelect).toHaveBeenCalledWith(2); // 古い id=1 を掴んでいない
  });

  it('依存に入れたコールバック自体が毎回新しいと安定しない', () => {
    const childRenders: number[] = [];
    const { rerender } = render(<Row id={1} label="a" onSelect={() => {}} childRenders={childRenders} />);
    rerender(<Row id={1} label="a" onSelect={() => {}} childRenders={childRenders} />);
    expect(childRenders).toHaveLength(2);
  });
});
