// string-pad: std::format の配置指定・幅の Contract を検証する
#include <format>
#include <iomanip>
#include <sstream>
#include <string>

#include "check.hpp"

int main() {
  // 配置と既定
  CHECK(std::format("{:^8}", "abc") == "  abc   ");
  CHECK(std::format("{:>8}", "abc") == "     abc");
  CHECK(std::format("{:<8}", "abc") == "abc     ");
  CHECK(std::format("{:6}", "ab") == "ab    ");  // 文字列の既定は左寄せ
  CHECK(std::format("{:6}", 42) == "    42");    // 数値の既定は右寄せ
  CHECK(std::format("{:>6}", std::string("abc")) == "   abc");

  // 中央の余りは右側が多い
  CHECK(std::format("{:^5}", "ab") == " ab  ");
  CHECK(std::format("{:^4}", "abc") == "abc ");

  // 埋め文字
  CHECK(std::format("{:*^8}", "abc") == "**abc***");
  CHECK(std::format("{:_<6}", "abc") == "abc___");
  CHECK(std::format("{:-^9}", "abc") == "---abc---");
  {
    const std::string fmt = "{:{}<6}";
    std::string s = "abc";
    char fill = '*';
    CHECK_THROWS((void)std::vformat(fmt, std::make_format_args(s, fill)), std::format_error);
  }

  // 実行時の幅
  CHECK(std::format("{:>{}}", "abc", 8) == "     abc");
  CHECK(std::format("{:^{}}", "abc", 8) == "  abc   ");
  {
    const std::string fmt = "{:>{}}";
    std::string s = "abc";
    int zero = 0, negative = -1;
    double frac = 2.5;
    CHECK(std::vformat(fmt, std::make_format_args(s, zero)) == "abc");
    CHECK_THROWS((void)std::vformat(fmt, std::make_format_args(s, negative)), std::format_error);
    CHECK_THROWS((void)std::vformat(fmt, std::make_format_args(s, frac)), std::format_error);
  }

  // 幅以下ならそのまま。切り詰めは精度で
  CHECK(std::format("{:^2}", "abc") == "abc");
  CHECK(std::format("{:^3}", "abc") == "abc");
  CHECK(std::format("{:.2}", "abcdef") == "ab");
  CHECK(std::format("{:>6.2}", "abcdef") == "    ab");

  // 空文字
  CHECK(std::format("{:^8}", "") == "        ");
  CHECK(std::format("{:*^4}", "") == "****");

  // 幅の単位: どの版でもコードポイント数（2）では数えない
  const std::string wide = std::format("{:>6}", "あい");
  CHECK(wide != "    あい");
#if defined(_GLIBCXX_RELEASE) && _GLIBCXX_RELEASE >= 14
  CHECK(wide == "  あい");                         // 表示幅 4
  CHECK(std::format("{:>6}", "日本語") == "日本語");  // 表示幅 6
  CHECK(std::format("{:>5}", "ｶ") == "    ｶ");  // 半角カナは 1
#elif defined(_GLIBCXX_RELEASE)
  CHECK(wide == "あい");                            // UTF-8 で 6 バイト
  CHECK(std::format("{:>5}", "ｶ") == "  ｶ");    // 3 バイト
#endif

  // 引数を変更しない
  const std::string src = "abc";
  CHECK(std::format("{:>5}", src) == "  abc");
  CHECK(src == "abc");

  // Alternatives
  CHECK(std::format("{:06}", 42) == "000042");
  CHECK(std::format("{:06}", -42) == "-00042");
  std::ostringstream os;
  os << std::setw(8) << std::setfill('*') << std::right << "abc";
  CHECK(os.str() == "*****abc");
  CHECK(std::string(3, ' ') + "abc" == "   abc");

  FINISH();
}
