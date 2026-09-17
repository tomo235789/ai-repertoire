// カード pattern-context-split の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  CounterProvider,
  counterReducer,
  useCounterDispatch,
  useCounterState,
  type CounterAction,
  type CounterState,
} from './pattern-context-split';

function Display({ renders }: { renders: number[] }) {
  const { count, label } = useCounterState();
  renders.push(1);
  return (
    <p>
      {label}: {count}
    </p>
  );
}

function IncrementButton({ renders }: { renders: number[] }) {
  const dispatch = useCounterDispatch();
  renders.push(1);
  return <button onClick={() => dispatch({ type: 'increment' })}>+1</button>;
}

function Static({ renders }: { renders: number[] }) {
  renders.push(1);
  return <p>static</p>;
}

/** 比較用: state と dispatch を 1 つのオブジェクトで配る Context */
const MergedContext = createContext<{ state: CounterState; dispatch: Dispatch<CounterAction> } | null>(null);
function MergedProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(counterReducer, { count: 0, label: 'counter' });
  return <MergedContext value={{ state, dispatch }}>{children}</MergedContext>;
}
function MergedIncrementButton({ renders }: { renders: number[] }) {
  const { dispatch } = useContext(MergedContext)!;
  renders.push(1);
  return <button onClick={() => dispatch({ type: 'increment' })}>+1</button>;
}

describe('pattern-context-split', () => {
  afterEach(cleanup);

  it('state を使う子は更新のたびに再レンダーされ、dispatch だけ使う子は再レンダーされない', async () => {
    const user = userEvent.setup();
    const displayRenders: number[] = [];
    const buttonRenders: number[] = [];
    render(
      <CounterProvider>
        <Display renders={displayRenders} />
        <IncrementButton renders={buttonRenders} />
      </CounterProvider>,
    );
    await user.click(screen.getByText('+1'));
    await user.click(screen.getByText('+1'));
    expect(screen.getByText('counter: 2')).toBeInTheDocument();
    expect(displayRenders).toHaveLength(3);
    expect(buttonRenders).toHaveLength(1);
  });

  it('children として渡された、Context を使わない要素は Provider の更新で再レンダーされない', async () => {
    const user = userEvent.setup();
    const staticRenders: number[] = [];
    render(
      <CounterProvider>
        <Static renders={staticRenders} />
        <IncrementButton renders={[]} />
      </CounterProvider>,
    );
    await user.click(screen.getByText('+1'));
    expect(staticRenders).toHaveLength(1);
  });

  it('state と dispatch を 1 つのオブジェクトで配ると、dispatch だけ使う子も毎回再レンダーされる', async () => {
    const user = userEvent.setup();
    const buttonRenders: number[] = [];
    render(
      <MergedProvider>
        <MergedIncrementButton renders={buttonRenders} />
      </MergedProvider>,
    );
    await user.click(screen.getByText('+1'));
    expect(buttonRenders).toHaveLength(2);
  });

  it('reducer は純粋関数で、単体でテストできる', () => {
    const s0: CounterState = { count: 0, label: 'x' };
    const s1 = counterReducer(s0, { type: 'increment' });
    expect(s1).toEqual({ count: 1, label: 'x' });
    expect(s0).toEqual({ count: 0, label: 'x' }); // 入力を変更しない
    expect(counterReducer(s1, { type: 'rename', label: 'y' })).toEqual({ count: 1, label: 'y' });
  });

  it('Provider の外でフックを使うと例外を投げる', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Display renders={[]} />)).toThrow('useCounterState は CounterProvider の中で使う');
    expect(() => render(<IncrementButton renders={[]} />)).toThrow('useCounterDispatch は CounterProvider の中で使う');
    errorSpy.mockRestore();
  });
});
