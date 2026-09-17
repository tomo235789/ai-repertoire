// number-round-to: std::round(x * p) / p イディオムの Contract を検証する
#include <cfenv>
#include <cmath>
#include <format>
#include <limits>

#include "check.hpp"

double round_to(double x, int digits) {
  const double p = std::pow(10.0, digits);
  return std::round(x * p) / p;
}

int main() {
  // .5 は 0 から遠い方へ（偶数丸めではない）
  CHECK(std::round(0.5) == 1.0);
  CHECK(std::round(1.5) == 2.0);
  CHECK(std::round(2.5) == 3.0);
  CHECK(std::round(-2.5) == -3.0);
  CHECK(round_to(2.5, 0) == 3.0);
  CHECK(round_to(-2.5, 0) == -3.0);

  // 丸めモードを変えても std::round は影響されない（nearbyint は従う）
  std::fesetround(FE_TONEAREST);
  CHECK(std::nearbyint(2.5) == 2.0);
  CHECK(std::nearbyint(3.5) == 4.0);
  std::fesetround(FE_DOWNWARD);
  CHECK(std::round(2.5) == 3.0);
  CHECK(std::nearbyint(2.5) == 2.0);
  std::fesetround(FE_TONEAREST);

  // 桁指定
  CHECK(round_to(1.2345, 2) == 1.23);
  CHECK(round_to(1.2345, 0) == 1.0);
  CHECK(round_to(1.45, 1) == 1.5);
  CHECK(round_to(1250, -2) == 1300.0);
  CHECK(round_to(1234.5678, -2) == 1200.0);

  // 表現誤差はそのまま
  CHECK(1.005 * 100 == 100.49999999999999);
  CHECK(round_to(1.005, 2) == 1.0);
  CHECK(2.675 * 100 == 267.5);
  CHECK(round_to(2.675, 2) == 2.68);

  // NaN / inf / 極端な桁
  CHECK(std::isnan(round_to(std::numeric_limits<double>::quiet_NaN(), 2)));
  CHECK(round_to(std::numeric_limits<double>::infinity(), 2) == std::numeric_limits<double>::infinity());
  CHECK(round_to(-std::numeric_limits<double>::infinity(), 2) == -std::numeric_limits<double>::infinity());
  CHECK(std::isnan(round_to(1.005, 400)));
  CHECK(std::isnan(round_to(1.005, -400)));

  // 符号付き零
  CHECK(std::round(-0.4) == 0.0);
  CHECK(std::signbit(std::round(-0.4)));
  CHECK(std::signbit(round_to(-0.4, 0)));

  // Alternatives: 書式指定は 2 進数の値を正確に丸める
  CHECK(std::format("{:.2f}", 2.675) == "2.67");
  CHECK(std::format("{:.0f}", 2.5) == "2");
  CHECK(std::format("{:.2f}", 1.5) == "1.50");
  CHECK(std::lround(2.5) == 3L);
  CHECK(std::lround(-2.5) == -3L);
  CHECK(static_cast<int>(std::round(2.5)) == 3);
  CHECK(static_cast<int>(2.5) == 2);

  // Pitfalls: 負の桁は正の 10 のべき乗で割って掛ける（pow(10, -5) の丸めは実装依存なので round_to の値は検証しない）
  CHECK(std::round(123456 / 1e5) * 1e5 == 100000.0);

  FINISH();
}
