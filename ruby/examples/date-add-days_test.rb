# カード date-add-days の Contract を検証するテスト（Date#+）
require "minitest/autorun"
require "date"

class DateAddDaysTest < Minitest::Test
  LEAP = Date.new(2024, 2, 29)

  def test_adds_and_subtracts_days
    # 日数の加算・減算。next_day / prev_day も同じ
    assert_equal Date.new(2024, 3, 1), LEAP + 1
    assert_equal Date.new(2024, 2, 28), LEAP - 1
    assert_equal Date.new(2024, 3, 3), LEAP.next_day(3)
    assert_equal Date.new(2024, 2, 27), LEAP.prev_day(2)
    assert_equal Date.new(2024, 3, 1), LEAP.succ
  end

  def test_does_not_mutate_and_returns_new_instance
    # 入力を変更せず、+ 0 でも別インスタンス
    d = Date.new(2024, 2, 29)
    result = d + 0
    assert_equal Date.new(2024, 2, 29), d
    assert_equal d, result
    refute_same d, result
  end

  def test_calendar_carry_over
    # 月末・年末・うるう年の繰り越しはカレンダーどおり
    assert_equal Date.new(2025, 3, 1), LEAP + 366
    assert_equal Date.new(2025, 2, 28), LEAP + 365
    assert_equal Date.new(2025, 1, 1), Date.new(2024, 12, 31) + 1
    assert_equal Date.new(2023, 3, 1), Date.new(2023, 2, 28) + 1
  end

  def test_fractional_days_keep_hidden_day_fraction
    # 小数日は内部の時刻として保持され、同じ日付の Date と == で等しくならない
    half = LEAP + 1.5
    assert_instance_of Date, half
    assert_equal "2024-03-01", half.to_s
    assert_equal Rational(1, 2), half.day_fraction
    refute_equal Date.new(2024, 3, 1), half
    assert_operator half, :===, Date.new(2024, 3, 1)
    assert_equal Date.new(2024, 3, 2), half + 0.5
    assert_equal Rational(1, 2), (LEAP + Rational(3, 2)).day_fraction
    assert_equal Rational(0), (LEAP + 1).day_fraction
  end

  def test_datetime_advances_time
    # DateTime に小数を足すと時刻がそのまま進む
    dt = DateTime.new(2024, 2, 29, 13, 45, 7, "+09:00")
    assert_equal DateTime.new(2024, 3, 1, 13, 45, 7, "+09:00"), dt + 1
    assert_equal DateTime.new(2024, 3, 2, 1, 45, 7, "+09:00"), dt + 1.5
    assert_equal DateTime.new(2024, 2, 29, 14, 45, 7, "+09:00"), dt + Rational(1, 24)
  end

  def test_non_numeric_raises
    # 数値以外は TypeError。Infinity / NaN は FloatDomainError
    assert_raises(TypeError) { LEAP + "1" }
    assert_raises(TypeError) { LEAP + nil }
    assert_raises(TypeError) { LEAP + LEAP }
    assert_raises(FloatDomainError) { LEAP + Float::INFINITY }
    assert_raises(FloatDomainError) { LEAP + Float::NAN }
  end

  def test_date_minus_date_is_rational_days
    # Date - Date は日数の Rational
    diff = LEAP - Date.new(2024, 2, 1)
    assert_equal Rational(28, 1), diff
    assert_instance_of Rational, diff
    assert_equal 28, diff.to_i
  end

  def test_calendar_reform_is_respected
    # 既定の Date::ITALY では 1582-10-04 の翌日が 1582-10-15
    assert_equal "1582-10-15", (Date.new(1582, 10, 4) + 1).to_s
    assert_equal Date::ITALY, (LEAP + 1).start
  end

  def test_month_addition_clamps_to_end_of_month
    # Alternatives: >> は月末を最終日にクランプする
    assert_equal Date.new(2024, 2, 29), Date.new(2024, 1, 31) >> 1
    assert_equal Date.new(2023, 12, 31), Date.new(2024, 1, 31) << 1
    assert_equal Date.new(2025, 2, 28), LEAP >> 12
    assert_equal Date.new(2024, 3, 29), LEAP.next_month
  end

  def test_time_plus_is_seconds
    # Pitfalls: Time + 1 は 1 秒。日を足すなら 86400 か to_date
    t = Time.new(2024, 2, 29, 13, 45, 7, "+09:00")
    assert_equal Time.new(2024, 2, 29, 13, 45, 8, "+09:00"), t + 1
    assert_equal Time.new(2024, 3, 1, 13, 45, 7, "+09:00"), t + 86_400
    assert_equal Date.new(2024, 3, 1), t.to_date + 1
    assert_raises(TypeError) { t + t }
  end

  def test_range_enumeration
    # Alternatives: 日付の範囲を列挙できる
    assert_equal ["2024-02-29", "2024-03-01", "2024-03-02"], (LEAP..LEAP + 2).map(&:to_s)
    assert_equal 3, LEAP.step(LEAP + 2).count
  end
end
