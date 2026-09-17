// カード pattern-context-split の実装。state と dispatch を別の Context にして、dispatch だけ使う子の再レンダーを防ぐ
import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from 'react';

export type CounterState = { count: number; label: string };
export type CounterAction = { type: 'increment' } | { type: 'rename'; label: string };

const StateContext = createContext<CounterState | null>(null);
const DispatchContext = createContext<Dispatch<CounterAction> | null>(null);

export function counterReducer(state: CounterState, action: CounterAction): CounterState {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + 1 };
    case 'rename':
      return { ...state, label: action.label };
  }
}

/** state と dispatch を別々の Provider で配る。dispatch は useReducer が返す安定した参照 */
export function CounterProvider({ children, initial = { count: 0, label: 'counter' } }: { children: ReactNode; initial?: CounterState }) {
  const [state, dispatch] = useReducer(counterReducer, initial);
  return (
    <DispatchContext value={dispatch}>
      <StateContext value={state}>{children}</StateContext>
    </DispatchContext>
  );
}

export function useCounterState(): CounterState {
  const state = useContext(StateContext);
  if (state === null) throw new Error('useCounterState は CounterProvider の中で使う');
  return state;
}

export function useCounterDispatch(): Dispatch<CounterAction> {
  const dispatch = useContext(DispatchContext);
  if (dispatch === null) throw new Error('useCounterDispatch は CounterProvider の中で使う');
  return dispatch;
}
