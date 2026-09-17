// カード pattern-list-keys の実装。リストの key には安定した一意な値（id）を使う
import { useEffect } from 'react';

export type Row = { id: string; label: string };

/** 行ごとに非制御の input を持つ。key の付け方で並べ替え・削除時の挙動が変わる（index は比較用） */
export function EditableRows({ rows, keyBy = 'id', mountLog }: { rows: readonly Row[]; keyBy?: 'id' | 'index'; mountLog?: string[] }) {
  return (
    <ul>
      {rows.map((row, i) => (
        <RowItem key={keyBy === 'id' ? row.id : i} row={row} mountLog={mountLog} />
      ))}
    </ul>
  );
}

function RowItem({ row, mountLog }: { row: Row; mountLog?: string[] }) {
  useEffect(() => {
    mountLog?.push(`mount:${row.label}`);
    return () => {
      mountLog?.push(`unmount:${row.label}`);
    };
    // マウント・アンマウントだけ記録する。label は key で固定されている想定
  }, []);
  return (
    <li>
      <label>
        {row.label}
        <input defaultValue="" />
      </label>
    </li>
  );
}
