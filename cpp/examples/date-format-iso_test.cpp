// date-format-iso: std::format と <chrono> による ISO 8601 整形の Contract を検証する
#include <chrono>
#include <format>
#include <stdexcept>
#include <string>

#include "check.hpp"

int main() {
  using namespace std::chrono;
  const sys_seconds t = sys_days{2024y / 2 / 29} + 13h + 45min + 7s;

  // 基本形と各指定子
  CHECK(std::format("{:%FT%TZ}", t) == "2024-02-29T13:45:07Z");
  CHECK(std::format("{:%F}", t) == "2024-02-29");
  CHECK(std::format("{:%T}", t) == "13:45:07");
  CHECK(std::format("{:%FT%T%Z}", t) == "2024-02-29T13:45:07UTC");
  CHECK(std::format("{:%FT%T%z}", t) == "2024-02-29T13:45:07+0000");
  CHECK(std::format("{:%FT%T%Ez}", t) == "2024-02-29T13:45:07+00:00");
  CHECK(std::format("{:%Y%m%dT%H%M%SZ}", t) == "20240229T134507Z");
  CHECK(std::format("{}", t) == "2024-02-29 13:45:07");

  // 年は 4 桁ゼロ埋め。epoch 前も扱える
  CHECK(std::format("{:%F}", sys_days{1y / 1 / 1}) == "0001-01-01");
  CHECK(std::format("{:%FT%TZ}", sys_seconds{}) == "1970-01-01T00:00:00Z");
  CHECK(std::format("{:%FT%TZ}", sys_seconds{-1s}) == "1969-12-31T23:59:59Z");

  // 秒未満の桁は型の精度で決まり、floor で切り捨てる
  const auto tms = t + 123ms;
  CHECK(std::format("{:%FT%TZ}", tms) == "2024-02-29T13:45:07.123Z");
  CHECK(std::format("{:%FT%TZ}", t + 123456us) == "2024-02-29T13:45:07.123456Z");
  const auto tns = t + 999999999ns;
  CHECK(std::format("{:%FT%TZ}", tns) == "2024-02-29T13:45:07.999999999Z");
  CHECK(std::format("{:%FT%TZ}", floor<milliseconds>(tns)) == "2024-02-29T13:45:07.999Z");
  CHECK(std::format("{:%FT%TZ}", floor<seconds>(tns)) == "2024-02-29T13:45:07Z");
  const std::string now = std::format("{:%FT%TZ}", floor<seconds>(system_clock::now()));
  CHECK(now.size() == 20 && now[10] == 'T' && now.back() == 'Z');

  // zoned_time でタイムゾーン変換
  const zoned_time tokyo{"Asia/Tokyo", t};
  CHECK(std::format("{:%FT%T%Ez}", tokyo) == "2024-02-29T22:45:07+09:00");
  CHECK(std::format("{:%FT%T%Z}", tokyo) == "2024-02-29T22:45:07JST");
  CHECK(std::format("{:%FT%T%Ez}", zoned_time{"UTC", t}) == "2024-02-29T13:45:07+00:00");
  CHECK_THROWS(zoned_time("Not/A_Zone", t), std::runtime_error);
  const std::string local = std::format("{:%FT%T%Ez}", zoned_time{current_zone(), t});
  CHECK(local.size() == 25 && (local[19] == '+' || local[19] == '-'));

  // 日付型・local_time
  CHECK(std::format("{:%F}", 2024y / 2 / 29) == "2024-02-29");
  CHECK(std::format("{:%F}", sys_days{2024y / 2 / 29}) == "2024-02-29");
  CHECK(std::format("{:%FT%T}", sys_days{2024y / 2 / 29}) == "2024-02-29T00:00:00");
  const local_seconds lt = local_days{2024y / 2 / 29} + 13h + 45min + 7s;
  CHECK(std::format("{:%FT%T}", lt) == "2024-02-29T13:45:07");
  {
    const std::string fmt = "{:%FT%T%Z}";
    CHECK_THROWS((void)std::vformat(fmt, std::make_format_args(lt)), std::format_error);
  }

  // 入力を変更しない
  CHECK(t == sys_days{2024y / 2 / 29} + 13h + 45min + 7s);

  // Alternatives: 時刻部だけ
  CHECK(std::format("{:%T}", 13h + 45min + 7s) == "13:45:07");
  CHECK(std::format("{}", hh_mm_ss{13h + 45min + 7s + 123ms}) == "13:45:07.123");

  FINISH();
}
