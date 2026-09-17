// カード pattern-controlled-input の実装。value と onChange の組で入力を React の state に持つ
import { useRef, useState, type FormEvent } from 'react';

/** 制御された入力。表示される値は常に state。onChange で正規化（大文字化）もできる */
export function NameForm({ onSubmit, normalize }: { onSubmit: (name: string) => void; normalize?: (s: string) => string }) {
  const [name, setName] = useState('');
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(name.trim());
  };
  return (
    <form onSubmit={handleSubmit}>
      <input aria-label="名前" value={name} onChange={(e) => setName(normalize ? normalize(e.target.value) : e.target.value)} />
      <button type="button" onClick={() => setName('')}>
        クリア
      </button>
      <button type="submit" disabled={name.trim() === ''}>
        送信
      </button>
    </form>
  );
}

/** 非制御。DOM が値を持ち、送信時に ref から読む。入力中に再レンダーしない */
export function UncontrolledNameForm({ onSubmit, renders }: { onSubmit: (name: string) => void; renders?: number[] }) {
  const inputRef = useRef<HTMLInputElement>(null);
  renders?.push(1);
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(inputRef.current!.value.trim());
  };
  return (
    <form onSubmit={handleSubmit}>
      <input aria-label="名前" defaultValue="" ref={inputRef} />
      <button type="submit">送信</button>
    </form>
  );
}
