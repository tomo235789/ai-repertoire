# カード collection-dedup-by-key（Array#uniq）の Contract を検証するテスト
require "minitest/autorun"

class CollectionDedupByKeyTest < Minitest::Test
  Point = Struct.new(:x)

  class Opaque
    attr_reader :v
    def initialize(v)
      @v = v
    end
  end

  def test_keeps_first_occurrence_in_order
    # 順序を保ち、同じキーは最初に出現した要素を残す
    users = [{ id: 1, name: "a" }, { id: 2, name: "b" }, { id: 1, name: "c" }]
    assert_equal [{ id: 1, name: "a" }, { id: 2, name: "b" }], users.uniq { |u| u[:id] }
    assert_equal [3, 1, 2], [3, 1, 3, 2, 1].uniq
  end

  def test_does_not_mutate_receiver_and_keeps_references
    # レシーバを変更せず、返り値は要素の参照を共有する新しい配列
    first = { id: 1 }
    src = [first, { id: 1 }, { id: 2 }]
    result = src.uniq { |u| u[:id] }
    assert_equal [{ id: 1 }, { id: 1 }, { id: 2 }], src
    refute_same src, result
    assert_same first, result[0]
  end

  def test_block_is_called_once_per_element_when_two_or_more
    # 要素が 2 つ以上なら各要素に 1 回ずつ先頭から呼ばれ、1 つ以下なら呼ばれない
    seen = []
    [3, 1, 3].uniq { |x| seen << x; x }
    assert_equal [3, 1, 3], seen
    calls = 0
    [1].uniq { |x| calls += 1; x }
    assert_equal 0, calls
  end

  def test_without_block_uses_element_itself
    # ブロック省略時は要素そのものがキー
    assert_equal [1, 2], [1, 1, 2].uniq
  end

  def test_keys_are_compared_with_hash_and_eql
    # キーは hash / eql? で比較され、1 と 1.0 は別、配列は内容で同じ、独自クラスは同一性
    assert_equal [1, 1.0], [1, 1.0].uniq
    assert_equal ["a", :a], ["a", :a].uniq
    assert_equal [[1, 2]], [[1, 2], [1, 2]].uniq
    assert_equal [Point.new(1)], [Point.new(1), Point.new(1)].uniq
    assert_equal 2, [Opaque.new(1), Opaque.new(1)].uniq.size
  end

  def test_nan_keys_can_be_grouped_by_normalizing
    # NaN 同士は eql? で等しくないので、NaN をまとめたいならキーを正規化する（同一オブジェクトの扱いは実装依存）
    computed = 0.0 / 0.0
    refute_operator Float::NAN, :eql?, computed
    assert_equal 2, [Float::NAN, computed, 1.0].uniq { |x| x.nan? ? :nan : x }.size
  end

  def test_empty_input_returns_empty_array
    # 空配列は [] を返す
    assert_equal [], [].uniq { |x| x }
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝わる
    assert_raises(IOError) { [1, 2].uniq { |_x| raise IOError, "boom" } }
  end

  def test_bang_version_mutates_and_returns_nil_when_unchanged
    # uniq! はその場で除去し、変更が無ければ nil を返す
    src = [1, 1, 2]
    assert_same src, src.uniq!
    assert_equal [1, 2], src
    assert_nil [1, 2].uniq!
  end
end
