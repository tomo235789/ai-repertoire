# カード number-clamp の Contract を検証するテスト（Comparable#clamp）
require "minitest/autorun"
require "date"

class NumberClampTest < Minitest::Test
  def test_clamps_to_bounds_inclusive
    # 範囲外は境界値に、範囲内はそのまま。境界値は含む
    assert_equal 100, 120.clamp(0, 100)
    assert_equal 0, -5.clamp(0, 100)
    assert_equal 42, 42.clamp(0, 100)
    assert_equal 0, 0.clamp(0, 100)
    assert_equal 100, 100.clamp(0, 100)
  end

  def test_range_form_and_endless_ranges
    # Range 版と、端無し Range による片側のみの制限
    assert_equal 100, 120.clamp(0..100)
    assert_equal 42, 42.clamp(0..100)
    assert_equal 100, 120.clamp(..100)
    assert_equal(-5, -5.clamp(..100))
    assert_equal 0, -5.clamp(0..)
    assert_equal 120, 120.clamp(0..)
  end

  def test_returns_argument_object_without_conversion
    # 返り値は self / min / max のオブジェクトそのもので、型変換しない
    x = 5
    assert_same x, x.clamp(0, 10)
    assert_equal 9.5, 10.clamp(0.5, 9.5)
    assert_instance_of Float, 10.clamp(0.5, 9.5)
    assert_instance_of Integer, 5.clamp(0.5, 9.5)
  end

  def test_min_greater_than_max_raises
    # min > max は ArgumentError
    assert_raises(ArgumentError) { 5.clamp(10, 1) }
    assert_raises(ArgumentError) { 5.clamp(10..1) }
  end

  def test_exclusive_range_with_end_raises_but_endless_is_fine
    # 終端がある排他的な Range は ArgumentError。終端の無い 0... は 0.. と同じ
    assert_raises(ArgumentError) { 5.clamp(0...10) }
    assert_raises(ArgumentError) { 5.clamp(...10) }
    assert_equal 5, 5.clamp(0...)
    assert_equal 0, -5.clamp(0...)
  end

  def test_nil_bound_means_unbounded
    # min / max に nil を渡すとその側の制限を設けない
    assert_equal 5, 5.clamp(nil, 10)
    assert_equal 120, 120.clamp(0, nil)
    assert_equal 5, 5.clamp(nil, nil)
  end

  def test_nan_raises_instead_of_returning_nan
    # NaN が混ざると ArgumentError
    assert_raises(ArgumentError) { Float::NAN.clamp(0, 100) }
    assert_raises(ArgumentError) { 5.clamp(Float::NAN, 100) }
    assert_raises(ArgumentError) { 200.clamp(0, Float::NAN) }
  end

  def test_incomparable_types_raise
    # 比較できない型は ArgumentError
    assert_raises(ArgumentError) { 5.clamp(0, "a") }
  end

  def test_single_non_range_argument_raises_type_error
    # Pitfalls: 引数 1 個は Range のみ。数値 1 個は TypeError
    assert_raises(TypeError) { 5.clamp(10) }
  end

  def test_works_for_any_comparable
    # Alternatives: 文字列や Date にもそのまま使える
    assert_equal "c", "z".clamp("a", "c")
    assert_equal Date.new(2024, 2, 1), Date.new(2024, 1, 1).clamp(Date.new(2024, 2, 1), Date.new(2024, 3, 1))
  end
end
