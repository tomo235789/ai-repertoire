// カード function-once の Contract を検証するテスト
package examples

import (
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestFunctionOnce(t *testing.T) {
	t.Run("1 回目だけ実行し、以後は同じ戻り値（同じ参照）を返す", func(t *testing.T) {
		calls := 0
		load := sync.OnceValue(func() map[string]string {
			calls++
			return map[string]string{"mode": "test"}
		})
		a := load()
		b := load()
		if calls != 1 {
			t.Errorf("calls = %d", calls)
		}
		a["extra"] = "x"
		if b["extra"] != "x" {
			t.Errorf("同じマップではない")
		}
	})

	t.Run("複数の goroutine から同時に呼んでも 1 回だけ実行される", func(t *testing.T) {
		var calls atomic.Int32
		once := sync.OnceValue(func() int {
			calls.Add(1)
			time.Sleep(5 * time.Millisecond)
			return 42
		})
		var wg sync.WaitGroup
		for range 10 {
			wg.Add(1)
			go func() {
				defer wg.Done()
				if got := once(); got != 42 {
					t.Errorf("once() = %d", got)
				}
			}()
		}
		wg.Wait()
		if calls.Load() != 1 {
			t.Errorf("calls = %d", calls.Load())
		}
	})

	t.Run("panic すると以後の呼び出しも同じ値で panic し、f は再実行されない", func(t *testing.T) {
		calls := 0
		once := sync.OnceValue(func() int { calls++; panic("boom") })
		for range 2 {
			func() {
				defer func() {
					if r := recover(); r != "boom" {
						t.Errorf("recover = %v", r)
					}
				}()
				once()
			}()
		}
		if calls != 1 {
			t.Errorf("calls = %d", calls)
		}
	})

	t.Run("状態は返り値ごとに独立", func(t *testing.T) {
		o1 := sync.OnceValue(func() int { return 1 })
		o2 := sync.OnceValue(func() int { return 2 })
		if o1() != 1 || o2() != 2 {
			t.Errorf("独立していない")
		}
	})

	t.Run("nil を渡すと最初の呼び出し時に panic", func(t *testing.T) {
		once := sync.OnceValue[int](nil) // 作成時は panic しない
		defer func() {
			if r := recover(); r == nil {
				t.Errorf("panic しなかった")
			}
		}()
		once()
	})

	t.Run("OnceValues はエラーもキャッシュし再試行しない", func(t *testing.T) {
		calls := 0
		load := sync.OnceValues(func() (string, error) { calls++; return "", errors.New("fail") })
		_, e1 := load()
		_, e2 := load()
		if calls != 1 || e1 == nil || e1 != e2 {
			t.Errorf("calls=%d e1=%v e2=%v", calls, e1, e2)
		}
	})
}
