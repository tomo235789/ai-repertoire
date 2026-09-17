// カード pattern-derived-state の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { FilteredList, Total, TotalViaEffect, type Item } from './pattern-derived-state';

const items: Item[] = [
  { id: 1, name: 'apple', price: 100 },
  { id: 2, name: 'banana', price: 200 },
  { id: 3, name: 'apricot', price: 300 },
];

describe('pattern-derived-state', () => {
  afterEach(cleanup);

  it('レンダー中に計算した値は最初のレンダーから正しく、レンダーは 1 回で済む', () => {
    const renders: number[] = [];
    render(<Total items={items} renders={renders} />);
    expect(screen.getByText('合計: 600')).toBeInTheDocument();
    expect(renders).toEqual([600]);
  });

  it('props が変わると同じレンダーで新しい値になる（同期のずれが無い）', () => {
    const renders: number[] = [];
    const { rerender } = render(<Total items={items} renders={renders} />);
    rerender(<Total items={items.slice(0, 1)} renders={renders} />);
    expect(screen.getByText('合計: 100')).toBeInTheDocument();
    expect(renders).toEqual([600, 100]);
  });

  it('useEffect で setState する同期 effect は初回が古い値で描画され、レンダーが 1 回余分に走る', () => {
    const renders: number[] = [];
    const { rerender } = render(<TotalViaEffect items={items} renders={renders} />);
    // マウント時: 0 で描画 → effect で setState → 600 で再描画
    expect(renders).toEqual([0, 600]);
    rerender(<TotalViaEffect items={items.slice(0, 1)} renders={renders} />);
    // 更新時: 古い 600 で 1 回描画してから 100 になる（1 レンダー遅れる）
    expect(renders).toEqual([0, 600, 600, 100]);
    expect(screen.getByText('合計: 100')).toBeInTheDocument();
  });

  it('useMemo は依存が同じ間は通常は再計算を省略し、依存が変わったときは再計算する', async () => {
    const computeLog: string[] = [];
    function Parent() {
      const [query, setQuery] = useState('ap');
      const [tick, setTick] = useState(0);
      return (
        <>
          <button onClick={() => setTick(tick + 1)}>tick {tick}</button>
          <button onClick={() => setQuery('ban')}>query</button>
          <FilteredList items={items} query={query} computeLog={computeLog} />
        </>
      );
    }
    const user = userEvent.setup();
    render(<Parent />);
    expect(screen.getAllByRole('listitem').map((li) => li.textContent)).toEqual(['apple', 'apricot']);
    expect(computeLog).toEqual(['ap']);

    await user.click(screen.getByText('tick 0')); // 無関係な state 更新で親が再レンダー
    expect(screen.getByText('tick 1')).toBeInTheDocument();
    expect(computeLog).toEqual(['ap']); // 通常は再計算が省略される（React が保証する意味論ではない）

    await user.click(screen.getByText('query'));
    expect(screen.getAllByRole('listitem').map((li) => li.textContent)).toEqual(['banana']);
    expect(computeLog).toEqual(['ap', 'ban']);
  });

  it('useMemo の依存に毎回新しい配列を渡すと毎回再計算される', () => {
    const computeLog: string[] = [];
    const { rerender } = render(<FilteredList items={[...items]} query="a" computeLog={computeLog} />);
    rerender(<FilteredList items={[...items]} query="a" computeLog={computeLog} />);
    expect(computeLog).toEqual(['a', 'a']);
  });
});
