// カード pattern-controlled-input の Contract を検証するテスト
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { NameForm, UncontrolledNameForm } from './pattern-controlled-input';

describe('pattern-controlled-input', () => {
  afterEach(cleanup);

  it('入力するたびに onChange で state が更新され、DOM の value は state と一致する', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<NameForm onSubmit={onSubmit} />);
    const input = screen.getByLabelText<HTMLInputElement>('名前');
    expect(screen.getByText('送信')).toBeDisabled(); // 空のときは送信できない（state から導出）
    await user.type(input, ' alice ');
    expect(input).toHaveValue(' alice ');
    expect(screen.getByText('送信')).toBeEnabled();
    await user.click(screen.getByText('送信'));
    expect(onSubmit).toHaveBeenCalledWith('alice');
  });

  it('state を変えれば DOM の値も変わる（state が唯一の情報源）', async () => {
    const user = userEvent.setup();
    render(<NameForm onSubmit={() => {}} />);
    const input = screen.getByLabelText<HTMLInputElement>('名前');
    await user.type(input, 'alice');
    await user.click(screen.getByText('クリア'));
    expect(input).toHaveValue('');
    expect(screen.getByText('送信')).toBeDisabled();
  });

  it('onChange で正規化した値を state に入れると、表示もその値になる', async () => {
    const user = userEvent.setup();
    render(<NameForm onSubmit={() => {}} normalize={(s) => s.toUpperCase()} />);
    const input = screen.getByLabelText<HTMLInputElement>('名前');
    await user.type(input, 'abc');
    expect(input).toHaveValue('ABC');
  });

  it('value だけ渡して onChange を省くと React が警告し、入力しても値は変わらない', async () => {
    const user = userEvent.setup();
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(<input aria-label="固定" value="fixed" />);
    expect(errorSpy.mock.calls[0][0]).toContain('without an `onChange` handler');
    const input = screen.getByLabelText<HTMLInputElement>('固定');
    await user.type(input, 'x');
    expect(input).toHaveValue('fixed');
    errorSpy.mockRestore();
  });

  it('非制御（defaultValue + ref）は入力中に再レンダーせず、送信時に ref から値を読む', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const renders: number[] = [];
    render(<UncontrolledNameForm onSubmit={onSubmit} renders={renders} />);
    await user.type(screen.getByLabelText('名前'), ' bob ');
    expect(renders).toHaveLength(1);
    await user.click(screen.getByText('送信'));
    expect(onSubmit).toHaveBeenCalledWith('bob');
  });
});
