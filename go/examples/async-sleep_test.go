// カード async-sleep の Contract を検証するテスト
package examples

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestAsyncSleep(t *testing.T) {
	t.Run("少なくとも d の間止まる", func(t *testing.T) {
		start := time.Now()
		time.Sleep(10 * time.Millisecond)
		if got := time.Since(start); got < 10*time.Millisecond {
			t.Errorf("経過 = %v", got)
		}
	})

	t.Run("0 以下なら即座に返り panic しない", func(t *testing.T) {
		// 上限時間は環境依存で不安定になるので測らず、ブロックも panic もしないことだけ確認する
		time.Sleep(-time.Second)
		time.Sleep(0)
	})

	t.Run("他の goroutine は動き続ける", func(t *testing.T) {
		done := make(chan struct{})
		go func() {
			time.Sleep(time.Millisecond) // この goroutine の Sleep も呼び出し元を止めない
			close(done)
		}()
		time.Sleep(5 * time.Millisecond)
		select {
		case <-done:
		case <-time.After(5 * time.Second):
			t.Errorf("goroutine が動いていない")
		}
	})

	t.Run("select で context と組み合わせればキャンセルで抜けられる", func(t *testing.T) {
		ctx, cancel := context.WithCancel(context.Background())
		go func() {
			time.Sleep(5 * time.Millisecond)
			cancel()
		}()
		select {
		case <-time.After(time.Second):
			t.Errorf("タイマーが先に発火した")
		case <-ctx.Done():
			if !errors.Is(ctx.Err(), context.Canceled) {
				t.Errorf("Err = %v", ctx.Err())
			}
		}
	})

	t.Run("期限なら DeadlineExceeded", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Millisecond)
		defer cancel()
		select {
		case <-time.After(time.Second):
			t.Errorf("タイマーが先に発火した")
		case <-ctx.Done():
			if !errors.Is(ctx.Err(), context.DeadlineExceeded) {
				t.Errorf("Err = %v", ctx.Err())
			}
		}
	})

	t.Run("Duration はナノ秒単位", func(t *testing.T) {
		if time.Duration(500) != 500*time.Nanosecond {
			t.Errorf("Duration(500) = %v", time.Duration(500))
		}
		if 500*time.Millisecond != time.Duration(500_000_000) {
			t.Errorf("500ms = %v", 500*time.Millisecond)
		}
	})
}
