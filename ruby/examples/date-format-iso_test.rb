# カード date-format-iso の Contract を検証するテスト（Time#iso8601）
require "minitest/autorun"
require "time"
require "date"

class DateFormatIsoTest < Minitest::Test
  def jst
    Time.new(2024, 2, 29, 13, 45, 7.123456r, "+09:00")
  end

  def test_formats_with_receiver_offset
    # レシーバのオフセットで整形し、utc? なら Z
    assert_equal "2024-02-29T13:45:07+09:00", jst.iso8601
    assert_equal "2024-02-29T13:45:07-03:00", Time.new(2024, 2, 29, 13, 45, 7, "-03:00").iso8601
    assert_equal "2024-02-29T04:45:07Z", Time.utc(2024, 2, 29, 4, 45, 7).iso8601
    assert_equal "2024-02-29T04:45:07Z", jst.getutc.iso8601
  end

  def test_zero_offset_without_utc_flag_is_not_z
    # オフセット 0 でも utc? が偽なら +00:00
    t = Time.new(2024, 2, 29, 13, 45, 7, "+00:00")
    refute_predicate t, :utc?
    assert_equal "2024-02-29T13:45:07+00:00", t.iso8601
    assert_equal "2024-02-29T13:45:07Z", Time.new(2024, 2, 29, 13, 45, 7, "UTC").iso8601
  end

  def test_fraction_digits_are_fixed_and_truncated
    # 正の桁数を指定すると桁数固定・切り捨てで、小数秒が 0 でも .000 を出す。0（既定）なら小数秒を出さない
    assert_equal "2024-02-29T13:45:07.123+09:00", jst.iso8601(3)
    assert_equal "2024-02-29T13:45:07.123456+09:00", jst.iso8601(6)
    assert_equal "2024-02-29T04:45:07.000Z", Time.utc(2024, 2, 29, 4, 45, 7).iso8601(3)
    assert_equal "2024-02-29T13:45:07.999+09:00", Time.new(2024, 2, 29, 13, 45, 7.9999r, "+09:00").iso8601(3)
    assert_equal "2024-02-29T13:45:07.1234560000+09:00", jst.iso8601(10)
  end

  def test_year_padding
    # 年は 4 桁ゼロ埋め。5 桁以上や負の年はそのまま
    assert_equal "0001-01-01T00:00:00Z", Time.utc(1, 1, 1).iso8601
    assert_equal "12345-01-01T00:00:00Z", Time.utc(12345, 1, 1).iso8601
    assert_equal "-0001-01-01T00:00:00Z", Time.utc(-1, 1, 1).iso8601
  end

  def test_invalid_fraction_digits_raise
    # fraction_digits が整数に変換できないと TypeError（3.4 以降の core 実装。3.3 以前の time gem 実装は to_i で受け入れる）
    assert_raises(TypeError) { jst.iso8601("3") }
    assert_raises(TypeError) { jst.iso8601(nil) }
  end

  def test_does_not_mutate_and_xmlschema_is_alias
    # 入力を変更せず、xmlschema は同じ結果
    t = jst
    t.iso8601
    assert_equal 32400, t.utc_offset
    assert_equal t.iso8601, t.xmlschema
  end

  def test_date_and_datetime
    # Date#iso8601 は日付のみ、DateTime#iso8601(n) は Time と同じ形式
    assert_equal "2024-02-29", Date.new(2024, 2, 29).iso8601
    assert_equal "2024-02-29", jst.to_date.iso8601
    assert_equal "2024-02-29T13:45:07+09:00", DateTime.new(2024, 2, 29, 13, 45, 7, "+09:00").iso8601
    assert_equal "2024-02-29T13:45:07.000+09:00", DateTime.new(2024, 2, 29, 13, 45, 7, "+09:00").iso8601(3)
  end

  def test_parse_round_trip
    # Time.iso8601 は逆変換。オフセットを保ち、Z は utc?、オフセット無しはローカル
    parsed = Time.iso8601("2024-02-29T13:45:07+09:00")
    assert_equal 32400, parsed.utc_offset
    assert_equal Time.new(2024, 2, 29, 13, 45, 7, "+09:00"), parsed
    assert_predicate Time.iso8601("2024-02-29T04:45:07Z"), :utc?
    assert_equal 123_000_000, Time.iso8601("2024-02-29T04:45:07.123Z").nsec
    assert_equal jst.floor(3), Time.iso8601(jst.iso8601(3))
    local = Time.iso8601("2024-02-29T13:45:07")
    assert_equal Time.local(2024, 2, 29, 13, 45, 7), local
  end

  def test_parse_rejects_other_formats
    # 日付のみ・空白区切り・basic 形式は ArgumentError（time gem の正規表現は - 区切りと T が必須）
    assert_raises(ArgumentError) { Time.iso8601("2024-02-29") }
    assert_raises(ArgumentError) { Time.iso8601("2024-02-29 13:45:07") }
    assert_raises(ArgumentError) { Time.iso8601("20240229T134507Z") }
  end

  def test_utc_is_destructive_but_getutc_is_not
    # Pitfalls: Time#utc はレシーバを書き換える。getutc は書き換えない
    t = Time.new(2024, 2, 29, 13, 45, 7, "+09:00")
    assert_equal "2024-02-29T04:45:07Z", t.getutc.iso8601
    assert_equal "2024-02-29T13:45:07+09:00", t.iso8601
    t.utc
    assert_equal "2024-02-29T04:45:07Z", t.iso8601
  end

  def test_to_s_and_strftime_alternatives
    # Alternatives / Pitfalls: to_s は ISO 8601 ではない。strftime の %:z はコロン付き
    assert_equal "2024-02-29 13:45:07 +0900", jst.to_s
    assert_equal "2024-02-29T13:45:07+09:00", jst.strftime("%FT%T%:z")
    assert_equal "2024-02-29T13:45:07+0900", jst.strftime("%FT%T%z")
  end
end
