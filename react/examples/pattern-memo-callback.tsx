// カード pattern-memo-callback の実装。memo 化した子に渡すコールバックを useCallback で安定させる
import { memo, useCallback, useState } from 'react';

/** memo 化した子。props が前回と同じ（Object.is）なら再レンダーされない */
export const IncrementButton = memo(function IncrementButton({
  onClick,
  renders,
}: {
  onClick: () => void;
  renders?: number[];
}) {
  renders?.push(1);
  return <button onClick={onClick}>+1</button>;
});

/** 親。theme の更新では子を再レンダーさせない */
export function Toolbar({ childRenders }: { childRenders?: number[] }) {
  const [count, setCount] = useState(0);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  // 関数型更新にすれば count に依存しないので依存配列は空でよい
  const increment = useCallback(() => setCount((c) => c + 1), []);
  return (
    <div data-theme={theme}>
      <p>count: {count}</p>
      <button onClick={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}>theme: {theme}</button>
      <IncrementButton onClick={increment} renders={childRenders} />
    </div>
  );
}

export const SelectButton = memo(function SelectButton({
  onSelect,
  renders,
}: {
  onSelect: () => void;
  renders?: number[];
}) {
  renders?.push(1);
  return <button onClick={onSelect}>select</button>;
});

/** 依存する値（id）が変わったときだけ新しい関数になる */
export function Row({
  id,
  label,
  onSelect,
  childRenders,
}: {
  id: number;
  label: string;
  onSelect: (id: number) => void;
  childRenders?: number[];
}) {
  const handleSelect = useCallback(() => onSelect(id), [id, onSelect]);
  return (
    <div>
      <span>{label}</span>
      <SelectButton onSelect={handleSelect} renders={childRenders} />
    </div>
  );
}
