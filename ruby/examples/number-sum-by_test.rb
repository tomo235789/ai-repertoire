# カード number-sum-by の Contract を検証するテスト（Enumerable#sum）
require "minitest/autorun"
require "bigdecimal"

class NumberSumByTest < Minitest::Test
  def test_sums_values_extracted_by_block
    # ブロックで取り出した値を合計する
    items = [{ name: "a", qty: 2 }, { name: "b", qty: 3 }]
    assert_equal 5, items.sum { |item| item[:qty] }
    assert_equal 5, [2, 3].sum
  end

  def test_does_not_mutate_input
    # 入力を変更しない
    items = [0.1, 0.2]
    items.sum
    assert_equal [0.1, 0.2], items
  end

  def test_block_is_called_once_per_element_in_order
    # ブロックは各要素につき 1 回、先頭から順に呼ばれる
    calls = []
    [3, 1, 2].sum { |x| calls << x; x }
    assert_equal [3, 1, 2], calls
  end

  def test_empty_returns_init
    # 空なら init を返す。既定は Integer の 0
    assert_equal 0, [].sum
    assert_equal 0, [].sum { |x| x }
    assert_equal 0.0, [].sum(0.0)
    assert_instance_of Float, [].sum(0.0)
  end

  def test_no_type_conversion
    # 型変換せず、String や nil が混ざると TypeError。Integer と Float の混在は Float
    assert_raises(TypeError) { ["a", "b"].sum }
    assert_raises(TypeError) { [1, nil].sum }
    assert_raises(TypeError) { [{ qty: 1 }, {}].sum { |item| item[:qty] } }
    assert_equal 3.5, [1, 2.5].sum
    assert_instance_of Float, [1, 2.5].sum
    assert_instance_of Float, [1, 2].sum(0.0)
  end

  def test_float_sum_is_compensated
    # Float の合計は Kahan-Babuska 補正付き。inject(:+) は素朴な加算
    assert_equal 1.0, ([0.1] * 10).sum
    assert_equal 0.9999999999999999, ([0.1] * 10).inject(:+)
    assert_equal 0.6, [0.1, 0.2, 0.3].sum
    assert_equal 0.6000000000000001, [0.1, 0.2, 0.3].inject(:+)
    assert_equal 1.0, [1e100, 1.0, -1e100].sum
    assert_equal 0.0, [1e100, 1.0, -1e100].inject(:+)
    assert_equal 0.30000000000000004, [0.1, 0.2].sum
    assert_equal 1.0, ([0.1] * 10).sum(0.0)
  end

  def test_nan_and_infinity
    # NaN があれば NaN。+Infinity と -Infinity の両方があれば NaN
    assert_predicate [Float::NAN, 1].sum, :nan?
    assert_predicate [Float::INFINITY, -Float::INFINITY].sum, :nan?
    assert_equal Float::INFINITY, [Float::INFINITY, 1].sum
  end

  def test_rational_and_bigdecimal
    # Rational / BigDecimal の合計はそのまま動く。Float と混ぜると Float / BigDecimal に寄る
    assert_equal Rational(3, 2), [1, Rational(1, 2)].sum
    assert_equal 1.0, [Rational(1, 2), 0.5].sum
    assert_equal 1, ([BigDecimal("0.1")] * 10).sum
    assert_instance_of BigDecimal, [BigDecimal("0.1"), 0.1].sum
  end

  def test_range_and_hash
    # Range や Hash でも使える
    assert_equal 20, (1..4).sum { |x| x * 2 }
    assert_equal 3, { a: 1, b: 2 }.sum { |_k, v| v }
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝播する
    assert_raises(ArgumentError) { [1].sum { raise ArgumentError, "boom" } }
  end

  def test_exceptions_from_plus_coerce_and_each_propagate
    # 要素の + / coerce や each が投げた例外も TypeError に包まれず伝播する
    bad = Object.new
    def bad.coerce(_other) = raise IOError, "coerce"
    assert_raises(IOError) { [1, bad].sum }
    plus = Object.new
    def plus.+(_other) = raise IOError, "plus"
    assert_raises(IOError) { [1].sum(plus) }
    broken = Enumerator.new { |y| y << 1; raise IOError, "each" }
    assert_raises(IOError) { broken.sum }
  end

  def test_integer_range_sum_is_optimized_without_each
    # 整数 Range のブロック無し sum は each を呼ばずに計算される（実装の最適化。契約ではない）
    range_class = Class.new(Range) { def each = raise IOError, "each" }
    assert_equal 10, range_class.new(1, 4).sum
    assert_raises(IOError) { range_class.new(1, 4).sum { |x| x } }
  end

  def test_string_and_array_need_init
    # Alternatives: 文字列や配列は init を指定すれば動く
    assert_equal "ab", ["a", "b"].sum("")
    assert_equal [1, 2], [[1], [2]].sum([])
  end
end
