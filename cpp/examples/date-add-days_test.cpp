// date-add-days: std::chrono::sys_days + days の Contract を検証する
#include <chrono>

#include "check.hpp"

int main() {
  using namespace std::chrono;
  const sys_days d = 2024y / 2 / 29;

  // 暦どおりの繰り越し。元は変わらない
  CHECK(year_month_day{d + days{1}} == 2024y / 3 / 1);
  CHECK(year_month_day{d - days{1}} == 2024y / 2 / 28);
  CHECK(year_month_day{d + days{366}} == 2025y / 3 / 1);
  CHECK(year_month_day{d + days{365}} == 2025y / 2 / 28);
  CHECK(year_month_day{d + days{-400}} == 2023y / 1 / 25);
  CHECK(year_month_day{sys_days{2024y / 12 / 31} + days{1}} == 2025y / 1 / 1);
  CHECK(year_month_day{d} == 2024y / 2 / 29);
  const int n = 3;
  CHECK(year_month_day{d + days{n}} == 2024y / 3 / 3);

  // days{1} は 24 時間。時刻付きに足しても時刻は保たれる
  CHECK(days{1} == 24h);
  static_assert(days::period::num == 86400 && days::period::den == 1);
  const sys_seconds t = d + 13h + 45min + 7s;
  CHECK(t + days{1} == sys_days{2024y / 3 / 1} + 13h + 45min + 7s);
  CHECK(t - days{1} == sys_days{2024y / 2 / 28} + 13h + 45min + 7s);
  CHECK((t + days{1}) - t == 24h);
  CHECK(year_month_day{floor<days>(t + days{1})} == 2024y / 3 / 1);

  // year_month_day との相互変換と正規化
  const year_month_day bad = 2023y / 2 / 29;
  CHECK(!bad.ok());
  CHECK(year_month_day{sys_days{bad}} == 2023y / 3 / 1);
  const year_month_day m = year_month_day{2024y / 1 / 31} + months{1};
  CHECK(!m.ok());
  CHECK(m == 2024y / 2 / 31);
  CHECK(year_month_day{sys_days{m}} == 2024y / 3 / 2);
  CHECK(year_month_day{sys_days{2024y / 1 / 31} + days{31}} == 2024y / 3 / 2);

  // constexpr
  static_assert(year_month_day{sys_days{2024y / 2 / 29} + days{1}} == 2024y / 3 / 1);

  // Alternatives: 週、月末に丸める、差、zoned_time の壁時計
  CHECK(weeks{1} == days{7});
  CHECK(year_month_day{m.year() / m.month() / last} == 2024y / 2 / 29);
  CHECK(((d + days{1}) - d).count() == 1);
  const zoned_time ny{"America/New_York", local_days{2024y / 3 / 9} + 12h};
  const zoned_time by_sys{"America/New_York", ny.get_sys_time() + days{1}};
  const zoned_time by_local{"America/New_York", ny.get_local_time() + days{1}};
  CHECK(by_sys.get_local_time() == local_days{2024y / 3 / 10} + 13h);    // 夏時間開始で 1 時間ずれる
  CHECK(by_local.get_local_time() == local_days{2024y / 3 / 10} + 12h);  // 壁時計を保つ
  CHECK(by_local.get_sys_time() - ny.get_sys_time() == 23h);

  FINISH();
}
