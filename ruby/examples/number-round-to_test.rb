# カード number-round-to の Contract を検証するテスト（Float#round）
require "minitest/autorun"
require "bigdecimal"

class NumberRoundToTest < Minitest::Test
  def test_rounds_to_given_digits
    # 指定桁で丸める
    assert_equal 1, 1.2345.round
    assert_equal 1.23, 1.2345.round(2)
    assert_equal 1.235, 1.2345.round(3)
  end

  def test_return_type_depends_on_ndigits
    # ndigits 省略・0 以下は Integer、正なら Float
    assert_instance_of Integer, 1.2345.round
    assert_instance_of Integer, 1.2345.round(0)
    assert_instance_of Integer, 1234.5678.round(-2)
    assert_instance_of Float, 1.2345.round(2)
    assert_equal 1.0, 1.0.round(2)
  end

  def test_half_up_is_away_from_zero_by_default
    # 既定の half: :up は 0 から遠い方へ
    assert_equal 3, 2.5.round
    assert_equal(-3, -2.5.round)
    assert_equal 1, 0.5.round
    assert_equal 2, 1.5.round
  end

  def test_half_even_and_half_down
    # half: :even は偶数丸め、half: :down は 0 に近い方、nil は :up、不正な値は ArgumentError
    assert_equal 2, 2.5.round(half: :even)
    assert_equal 4, 3.5.round(half: :even)
    assert_equal(-2, -2.5.round(half: :even))
    assert_equal 2, 2.5.round(half: :down)
    assert_equal(-2, -2.5.round(half: :down))
    assert_equal 3, 2.5.round(half: nil)
    assert_raises(ArgumentError) { 2.5.round(half: :foo) }
  end

  def test_negative_ndigits_rounds_to_tens
    # 負の桁は 10 の位・100 の位で丸める
    assert_equal 1200, 1234.5678.round(-2)
    assert_equal 1300, 1250.0.round(-2)
  end

  def test_compensates_binary_representation_error
    # 2 進数の表現誤差を補正し、10 進の見た目どおりに丸める
    assert_equal 2.68, 2.675.round(2)
    assert_equal 1.01, 1.005.round(2)
    assert_equal 1.5, 1.45.round(1)
    assert_equal 2.68, 2.675.round(2, half: :even)
    assert_equal 2.66, 2.665.round(2, half: :even)
    assert_equal 2.67, 2.675.round(2, half: :down)
  end

  def test_nan_and_infinity
    # NaN / Infinity は ndigits 省略時に FloatDomainError、正の桁ならそのまま
    assert_raises(FloatDomainError) { Float::NAN.round }
    assert_raises(FloatDomainError) { Float::INFINITY.round }
    assert_predicate Float::NAN.round(2), :nan?
    assert_equal Float::INFINITY, Float::INFINITY.round(2)
  end

  def test_ndigits_type
    # ndigits の Float は切り捨て、String / nil は TypeError
    assert_equal 1.5, 1.5.round(1.5)
    assert_raises(TypeError) { 1.5.round("1") }
    assert_raises(TypeError) { 1.5.round(nil) }
  end

  def test_integer_round
    # Integer#round も half: を受け、負の桁で丸める。正の桁は何もしない
    assert_equal 20, 15.round(-1)
    assert_equal 30, 25.round(-1)
    assert_equal(-20, -15.round(-1))
    assert_equal 20, 15.round(-1, half: :even)
    assert_equal 20, 25.round(-1, half: :even)
    assert_equal 12, 12.round(2)
    assert_instance_of Integer, 12.round(2)
  end

  def test_format_rounds_differently_and_exact_alternatives
    # Alternatives: format の .5 の扱いは round と異なる。round してから format すれば揃う。BigDecimal / Rational は正確
    assert_equal "2", format("%.0f", 2.5)
    assert_equal "1.4", format("%.1f", 1.45)
    assert_equal "1.5", format("%.1f", 1.45.round(1))
    assert_equal "1.5", 1.5.round(2).to_s
    assert_equal BigDecimal("2.68"), BigDecimal("2.675").round(2)
    assert_equal Rational(268, 100), Rational("2.675").round(2)
    assert_equal 2.56, 2.567.floor(2)
    assert_equal 2.57, 2.567.ceil(2)
  end
end
