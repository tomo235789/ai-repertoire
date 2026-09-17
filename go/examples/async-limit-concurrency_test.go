// カード async-limit-concurrency の Contract を検証するテスト
package examples

import (
	"context"
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"

	"golang.org/x/sync/errgroup"
)

func TestAsyncLimitConcurrency(t *testing.T) {
	t.Run("同時に走る goroutine を n 個までに抑える", func(t *testing.T) {
		var g errgroup.Group
		g.SetLimit(2)
		var current, peak atomic.Int32
		for range 6 {
			g.Go(func() error {
				c := current.Add(1)
				for {
					p := peak.Load()
					if c <= p || peak.CompareAndSwap(p, c) {
						break
					}
				}
				time.Sleep(3 * time.Millisecond)
				current.Add(-1)
				return nil
			})
		}
		if err := g.Wait(); err != nil {
			t.Errorf("Wait = %v", err)
		}
		if peak.Load() != 2 {
			t.Errorf("peak = %d", peak.Load())
		}
	})

	t.Run("Go は枠が空くまでブロックし、TryGo は枠が無ければ false", func(t *testing.T) {
		var g errgroup.Group
		g.SetLimit(1)
		release := make(chan struct{})
		g.Go(func() error { <-release; return nil })
		start := time.Now()
		blocked := make(chan time.Duration, 1)
		go func() {
			g.Go(func() error { return nil })
			blocked <- time.Since(start)
		}()
		time.Sleep(10 * time.Millisecond)
		if g.TryGo(func() error { return nil }) {
			t.Errorf("TryGo が枠なしで起動した")
		}
		close(release)
		if got := <-blocked; got < 10*time.Millisecond {
			t.Errorf("Go がブロックしなかった: %v", got)
		}
		if err := g.Wait(); err != nil {
			t.Errorf("Wait = %v", err)
		}
	})

	t.Run("Wait は最初に非 nil を返した関数のエラーを返す。2 回呼んでも同じ", func(t *testing.T) {
		var g errgroup.Group
		g.SetLimit(2)
		errFirst := errors.New("returned-first")
		g.Go(func() error { time.Sleep(10 * time.Millisecond); return errors.New("submitted-first") })
		g.Go(func() error { return errFirst })
		if err := g.Wait(); err != errFirst {
			t.Errorf("Wait = %v", err)
		}
		if err := g.Wait(); err != errFirst {
			t.Errorf("2 回目の Wait = %v", err)
		}

		var g2 errgroup.Group
		base := errors.New("base")
		g2.Go(func() error { return fmt.Errorf("wrap: %w", base) })
		if err := g2.Wait(); !errors.Is(err, base) {
			t.Errorf("errors.Is が効かない: %v", err)
		}
		var g3 errgroup.Group
		g3.Go(func() error { return nil })
		if err := g3.Wait(); err != nil {
			t.Errorf("全部 nil = %v", err)
		}
	})

	t.Run("WithContext は最初のエラーで ctx をキャンセルし、Cause にそのエラーが入る", func(t *testing.T) {
		g, ctx := errgroup.WithContext(context.Background())
		g.SetLimit(2)
		failFast := errors.New("fail fast")
		var sawCancel atomic.Bool
		g.Go(func() error { return failFast })
		g.Go(func() error {
			select {
			case <-ctx.Done():
				sawCancel.Store(true)
				return ctx.Err()
			case <-time.After(500 * time.Millisecond):
				return nil
			}
		})
		if err := g.Wait(); err != failFast {
			t.Errorf("Wait = %v", err)
		}
		if !sawCancel.Load() || !errors.Is(ctx.Err(), context.Canceled) || context.Cause(ctx) != failFast {
			t.Errorf("sawCancel=%v Err=%v Cause=%v", sawCancel.Load(), ctx.Err(), context.Cause(ctx))
		}
	})

	t.Run("エラーが無くても Wait が返るとき ctx はキャンセルされる", func(t *testing.T) {
		g, ctx := errgroup.WithContext(context.Background())
		g.Go(func() error { return nil })
		if err := g.Wait(); err != nil || ctx.Err() == nil {
			t.Errorf("err=%v ctx.Err=%v", err, ctx.Err())
		}
	})

	t.Run("ctx がキャンセルされても、Wait の前なら後続の Go は起動する", func(t *testing.T) {
		g, ctx := errgroup.WithContext(context.Background())
		first := errors.New("first")
		g.Go(func() error { return first })
		<-ctx.Done() // 最初のエラーでキャンセル済み（Wait はまだ呼んでいない）
		var started atomic.Bool
		g.Go(func() error { started.Store(true); return ctx.Err() })
		if err := g.Wait(); err != first {
			t.Errorf("Wait = %v", err)
		}
		if !started.Load() {
			t.Errorf("起動しなかった")
		}
	})

	t.Run("n == 0 は新規起動を禁止、n < 0 は無制限、ゼロ値も無制限", func(t *testing.T) {
		var g0 errgroup.Group
		g0.SetLimit(0)
		if g0.TryGo(func() error { return nil }) {
			t.Errorf("limit 0 で起動した")
		}
		var gn errgroup.Group
		gn.SetLimit(-1)
		for range 3 {
			gn.Go(func() error { return nil })
		}
		if err := gn.Wait(); err != nil {
			t.Errorf("無制限 = %v", err)
		}
		var gz errgroup.Group
		if !gz.TryGo(func() error { return nil }) {
			t.Errorf("ゼロ値で起動しなかった")
		}
		if err := gz.Wait(); err != nil {
			t.Errorf("ゼロ値 = %v", err)
		}
	})

	t.Run("goroutine が動いている間の SetLimit は非対応。n >= 0 なら panic し、n < 0 は現在の実装では panic しない", func(t *testing.T) {
		var g errgroup.Group
		g.SetLimit(1)
		release := make(chan struct{})
		g.Go(func() error { <-release; return nil })
		func() {
			defer func() {
				if r := recover(); r == nil {
					t.Errorf("panic しなかった")
				}
			}()
			g.SetLimit(2)
		}()
		func() {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("n < 0 で panic した: %v", r)
				}
			}()
			g.SetLimit(-1)
		}()
		close(release)
		if err := g.Wait(); err != nil {
			t.Errorf("Wait = %v", err)
		}
	})
}
