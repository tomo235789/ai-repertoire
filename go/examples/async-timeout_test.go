// カード async-timeout の Contract を検証するテスト
package examples

import (
	"context"
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"
)

func TestAsyncTimeout(t *testing.T) {
	t.Run("期限が来ると Done が閉じ Err が DeadlineExceeded になる。それまでは nil", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
		defer cancel()
		if ctx.Err() != nil {
			t.Errorf("期限前の Err = %v", ctx.Err())
		}
		if dl, ok := ctx.Deadline(); !ok || time.Until(dl) > 10*time.Millisecond {
			t.Errorf("Deadline = %v %v", dl, ok)
		}
		<-ctx.Done()
		if !errors.Is(ctx.Err(), context.DeadlineExceeded) || ctx.Err() != context.DeadlineExceeded {
			t.Errorf("Err = %v", ctx.Err())
		}
		if errors.Is(ctx.Err(), context.Canceled) {
			t.Errorf("Canceled ではないはず")
		}
	})

	t.Run("cancel を先に呼ぶと Canceled", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		cancel()
		if !errors.Is(ctx.Err(), context.Canceled) || errors.Is(ctx.Err(), context.DeadlineExceeded) {
			t.Errorf("Err = %v", ctx.Err())
		}
	})

	t.Run("timeout が 0 以下なら返された時点で DeadlineExceeded", func(t *testing.T) {
		for _, d := range []time.Duration{0, -time.Second} {
			ctx, cancel := context.WithTimeout(context.Background(), d)
			if !errors.Is(ctx.Err(), context.DeadlineExceeded) {
				t.Errorf("timeout=%v: Err = %v", d, ctx.Err())
			}
			cancel()
		}
	})

	t.Run("親の期限や親のキャンセルが先なら親の理由になる", func(t *testing.T) {
		parent, pcancel := context.WithTimeout(context.Background(), 5*time.Millisecond)
		defer pcancel()
		child, ccancel := context.WithTimeout(parent, time.Second)
		defer ccancel()
		<-child.Done()
		if !errors.Is(child.Err(), context.DeadlineExceeded) {
			t.Errorf("親の期限: %v", child.Err())
		}

		parent2, pcancel2 := context.WithCancel(context.Background())
		child2, ccancel2 := context.WithTimeout(parent2, time.Second)
		defer ccancel2()
		pcancel2()
		<-child2.Done()
		if !errors.Is(child2.Err(), context.Canceled) {
			t.Errorf("親のキャンセル: %v", child2.Err())
		}
	})

	t.Run("ctx を見ない goroutine はタイムアウト後も走り続ける", func(t *testing.T) {
		var running atomic.Bool
		started := make(chan struct{})
		release := make(chan struct{})
		done := make(chan struct{})
		go func() {
			running.Store(true)
			close(started)
			<-release // ctx を見ずに、外から解放されるまで走り続ける
			running.Store(false)
			close(done)
		}()
		<-started // 起動を確認してからタイムアウトを始める（スケジューリング遅延を測らない）
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Millisecond)
		defer cancel()
		<-ctx.Done()
		if !running.Load() {
			t.Errorf("タイムアウト時点で goroutine が止まっている")
		}
		close(release)
		<-done
	})

	t.Run("ctx を見る処理は Done で中断できる", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Millisecond)
		defer cancel()
		work := func(ctx context.Context) error {
			select {
			case <-time.After(time.Second):
				return nil
			case <-ctx.Done():
				return fmt.Errorf("work: %w", ctx.Err())
			}
		}
		err := work(ctx)
		if !errors.Is(err, context.DeadlineExceeded) {
			t.Errorf("err = %v", err)
		}
		if err == context.DeadlineExceeded {
			t.Errorf("包まれたエラーは == では判定できないはず")
		}
	})

	t.Run("Cause は既定で Err と同じ。WithTimeoutCause で理由を差し替えられる", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), 0)
		defer cancel()
		if context.Cause(ctx) != context.DeadlineExceeded {
			t.Errorf("Cause = %v", context.Cause(ctx))
		}
		reason := errors.New("slow api")
		ctx2, cancel2 := context.WithTimeoutCause(context.Background(), time.Millisecond, reason)
		defer cancel2()
		<-ctx2.Done()
		if !errors.Is(ctx2.Err(), context.DeadlineExceeded) || context.Cause(ctx2) != reason {
			t.Errorf("Err = %v Cause = %v", ctx2.Err(), context.Cause(ctx2))
		}
	})
}
