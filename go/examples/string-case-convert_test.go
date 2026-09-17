// カード string-case-convert の Contract を検証するテスト
package examples

import (
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestStringCaseConvert(t *testing.T) {
	t.Run("4 つの命名規則に変換する", func(t *testing.T) {
		if got := lo.KebabCase("userProfileURL"); got != "user-profile-url" {
			t.Errorf("KebabCase = %q", got)
		}
		if got := lo.CamelCase("user_profile_url"); got != "userProfileUrl" {
			t.Errorf("CamelCase = %q", got)
		}
		if got := lo.SnakeCase("UserProfileURL"); got != "user_profile_url" {
			t.Errorf("SnakeCase = %q", got)
		}
		if got := lo.PascalCase("user-profile-url"); got != "UserProfileUrl" {
			t.Errorf("PascalCase = %q", got)
		}
	})

	t.Run("空文字・空白のみ・記号のみは空文字", func(t *testing.T) {
		for _, s := range []string{"", "   ", "---"} {
			if got := lo.KebabCase(s); got != "" {
				t.Errorf("KebabCase(%q) = %q", s, got)
			}
		}
	})

	t.Run("区切り文字・大文字境界・数字で分割し、数字は独立した単語になる", func(t *testing.T) {
		cases := map[string]string{"version2Update": "version-2-update", "md5": "md-5", "utf8": "utf-8", "user.profile": "user-profile", "foo  bar": "foo-bar"}
		for in, want := range cases {
			if got := lo.KebabCase(in); got != want {
				t.Errorf("KebabCase(%q) = %q, want %q", in, got, want)
			}
		}
		if got := lo.SnakeCase("utf8"); got != "utf_8" {
			t.Errorf("SnakeCase(utf8) = %q", got)
		}
	})

	t.Run("連続する大文字は略語として 1 語にまとめ、末尾で小文字が続けば分ける", func(t *testing.T) {
		cases := map[string]string{"XMLHttpRequest": "xml-http-request", "iOS": "i-os", "ABCdef": "ab-cdef", "getHTTPResponseCode": "get-http-response-code"}
		for in, want := range cases {
			if got := lo.KebabCase(in); got != want {
				t.Errorf("KebabCase(%q) = %q, want %q", in, got, want)
			}
		}
	})

	t.Run("CamelCase / PascalCase は数字を直前の単語に連結し、略語も先頭以外を小文字にする", func(t *testing.T) {
		camel := map[string]string{"version2Update": "version2Update", "md5": "md5", "a1b2": "a1B2", "URLParser": "urlParser", "1st place": "1StPlace"}
		for in, want := range camel {
			if got := lo.CamelCase(in); got != want {
				t.Errorf("CamelCase(%q) = %q, want %q", in, got, want)
			}
		}
		if got := lo.PascalCase("HTTPRequest"); got != "HttpRequest" {
			t.Errorf("PascalCase(HTTPRequest) = %q", got)
		}
	})

	t.Run("記号・絵文字は残らず、非 ASCII の文字は残る", func(t *testing.T) {
		if got := lo.KebabCase("hello 🐶 world"); got != "hello-world" {
			t.Errorf("絵文字: %q", got)
		}
		if got := lo.KebabCase("Don't"); got != "don-t" {
			t.Errorf("アポストロフィ: %q", got)
		}
		if got := lo.KebabCase("Crème Brûlée"); got != "crème-brûlée" {
			t.Errorf("アクセント: %q", got)
		}
		if got := lo.SnakeCase("日本語 テキスト"); got != "日本語_テキスト" {
			t.Errorf("日本語: %q", got)
		}
	})

	t.Run("4 関数とも lo.Words と同じ単語分割を使う", func(t *testing.T) {
		if got := lo.Words("XMLHttpRequest v2"); !slices.Equal(got, []string{"XML", "Http", "Request", "v", "2"}) {
			t.Errorf("Words = %q", got)
		}
	})
}
