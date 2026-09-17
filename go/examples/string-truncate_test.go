// カード string-truncate の Contract を検証するテスト
package examples

import (
	"testing"
	"unicode/utf8"

	"github.com/samber/lo"
)

func TestStringTruncate(t *testing.T) {
	text := "The quick brown fox jumps over the lazy dog"

	t.Run("length は省略記号を含めた最大ルーン数", func(t *testing.T) {
		if got := lo.Ellipsis(text, 30); got != "The quick brown fox jumps o..." {
			t.Errorf("Ellipsis(30) = %q", got)
		}
		if got := lo.Ellipsis(text, 20); got != "The quick brown f..." {
			t.Errorf("Ellipsis(20) = %q", got)
		}
		if got := utf8.RuneCountInString(lo.Ellipsis(text, 20)); got != 20 {
			t.Errorf("ルーン数 = %d", got)
		}
	})

	t.Run("ルーン単位で数え、バイト長ではない", func(t *testing.T) {
		got := lo.Ellipsis("日本語の文章です", 5)
		if got != "日本..." {
			t.Errorf("日本語 = %q", got)
		}
		if utf8.RuneCountInString(got) != 5 || len(got) != 9 {
			t.Errorf("runes=%d bytes=%d", utf8.RuneCountInString(got), len(got))
		}
		if got := lo.Ellipsis("🐶🐶🐶🐶🐶", 4); got != "🐶..." {
			t.Errorf("絵文字 = %q", got)
		}
		// ZWJ で結合した絵文字はコードポイントごとに分かれる
		family := "👨‍👩‍👧"
		if got := lo.Ellipsis(family+" family", 6); got != "👨‍👩..." {
			t.Errorf("ZWJ = %q", got)
		}
	})

	t.Run("前後の空白と切り位置の末尾の空白を落とす", func(t *testing.T) {
		if got := lo.Ellipsis("  padded text  ", 20); got != "padded text" {
			t.Errorf("TrimSpace = %q", got)
		}
		if got := lo.Ellipsis("hello world", 9); got != "hello..." {
			t.Errorf("末尾空白 = %q", got)
		}
	})

	t.Run("ルーン数が length 以下ならそのまま返す", func(t *testing.T) {
		if got := lo.Ellipsis(text, 43); got != text {
			t.Errorf("ちょうど = %q", got)
		}
		if got := lo.Ellipsis(text, 100); got != text {
			t.Errorf("余裕 = %q", got)
		}
		if got := lo.Ellipsis("ab", 2); got != "ab" {
			t.Errorf("短い = %q", got)
		}
	})

	t.Run("length が 3 以下で切り詰めが必要なら ... だけを返し length を超える", func(t *testing.T) {
		for _, l := range []int{3, 2, 1, 0, -1} {
			if got := lo.Ellipsis("abcd", l); got != "..." {
				t.Errorf("Ellipsis(abcd, %d) = %q", l, got)
			}
		}
		if got := lo.Ellipsis("abc", 3); got != "abc" {
			t.Errorf("Ellipsis(abc, 3) = %q", got)
		}
	})

	t.Run("空文字は空文字", func(t *testing.T) {
		if got := lo.Ellipsis("", 0); got != "" {
			t.Errorf("Ellipsis(\"\", 0) = %q", got)
		}
		if got := lo.Ellipsis("", 5); got != "" {
			t.Errorf("Ellipsis(\"\", 5) = %q", got)
		}
	})
}
