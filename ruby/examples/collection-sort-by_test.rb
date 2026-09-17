# カード collection-sort-by（Enumerable#sort_by）の Contract を検証するテスト
require "minitest/autorun"

class CollectionSortByTest < Minitest::Test
  def test_sorts_ascending_by_multiple_keys
    # 配列キーを左から順に比較して昇順に並べる
    users = [{ name: "b", age: 30 }, { name: "a", age: 30 }, { name: "c", age: 20 }]
    expected = [{ name: "c", age: 20 }, { name: "a", age: 30 }, { name: "b", age: 30 }]
    assert_equal expected, users.sort_by { |u| [u[:age], u[:name]] }
    assert_equal [3, 2, 1], [1, 3, 2].sort_by { |x| -x }
  end

  def test_unstable_but_keys_are_ordered_and_with_index_stabilizes
    # 同じキーの順は保証されないのでキー順だけを検証し、添字を加えれば安定化できる
    src = (0...100).map { |i| [i % 2, i] }
    result = src.sort_by { |k, _| k }
    assert_equal src.map(&:first).sort, result.map(&:first)
    assert_equal src.sort, result.sort
    stable = src.sort_by.with_index { |(k, _), i| [k, i] }
    assert_equal src.select { |k, _| k == 0 } + src.select { |k, _| k == 1 }, stable
  end

  def test_does_not_mutate_receiver_and_keeps_references
    # レシーバを変更せず、返り値は要素の参照を共有する新しい配列
    a = { v: 2 }
    src = [a, { v: 1 }]
    result = src.sort_by { |h| h[:v] }
    assert_equal [{ v: 2 }, { v: 1 }], src
    refute_same src, result
    assert_same a, result[1]
  end

  def test_returns_enumerator_without_block
    # ブロック無しは Enumerator を返す
    assert_instance_of Enumerator, [1].sort_by
  end

  def test_block_is_called_once_per_element_in_order
    # ブロックは各要素に 1 回ずつ先頭から呼ばれる
    seen = []
    [3, 1, 2].sort_by { |x| seen << x; x }
    assert_equal [3, 1, 2], seen
  end

  def test_empty_input_returns_empty_array
    # 空配列は [] を返す
    assert_equal [], [].sort_by { |x| x }
  end

  def test_incomparable_keys_raise_argument_error
    # nil・型の混在・NaN が混ざると ArgumentError、配列キーの中でも同じ
    assert_raises(ArgumentError) { [1, nil, 2].sort_by { |x| x } }
    assert_raises(ArgumentError) { [1, "a"].sort_by { |x| x } }
    assert_raises(ArgumentError) { [1.0, Float::NAN].sort_by { |x| x } }
    assert_raises(ArgumentError) { [[1, nil], [1, 2]].sort_by { |x| x } }
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝わる
    assert_raises(IOError) { [1, 2].sort_by { |_x| raise IOError, "boom" } }
  end
end
