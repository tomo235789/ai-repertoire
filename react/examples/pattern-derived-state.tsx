// カード pattern-derived-state の実装。state から導出できる値はレンダー中に計算する
import { useEffect, useMemo, useState } from 'react';

export type Item = { id: number; name: string; price: number };

const sum = (items: readonly Item[]): number => items.reduce((acc, it) => acc + it.price, 0);

/** 推奨: 合計は state にせず、レンダー中に props から計算する */
export function Total({ items, renders }: { items: readonly Item[]; renders?: number[] }) {
  const total = sum(items);
  renders?.push(total);
  return <p>合計: {total}</p>;
}

/** 高コストな導出は useMemo。依存 (items, query) が同じ間は通常は再計算を省略する（最適化であり保証ではない） */
export function FilteredList({
  items,
  query,
  computeLog,
}: {
  items: readonly Item[];
  query: string;
  computeLog?: string[];
}) {
  const filtered = useMemo(() => {
    computeLog?.push(query);
    return items.filter((it) => it.name.includes(query));
  }, [items, query]);
  return (
    <ul>
      {filtered.map((it) => (
        <li key={it.id}>{it.name}</li>
      ))}
    </ul>
  );
}

/** アンチパターン（比較用）: useEffect で state に同期する。1 レンダー遅れ、レンダー回数も増える */
export function TotalViaEffect({ items, renders }: { items: readonly Item[]; renders?: number[] }) {
  const [total, setTotal] = useState(0);
  useEffect(() => {
    setTotal(sum(items));
  }, [items]);
  renders?.push(total);
  return <p>合計: {total}</p>;
}
