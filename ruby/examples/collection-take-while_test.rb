# カード collection-take-while（Enumerable#take_while）の Contract を検証するテスト
require "minitest/autorun"

class CollectionTakeWhileTest < Minitest::Test
  def test_takes_prefix_until_first_falsy
    # 先頭から最初に偽になる直前までを順番どおり返す
    assert_equal [1, 2], [1, 2, 3, 4, 1].take_while { |x| x < 3 }
  end

  def test_does_not_mutate_receiver_and_keeps_references
    # レシーバを変更せず、返り値は要素の参照を共有する新しい配列
    a = { v: 1 }
    src = [a, { v: 2 }]
    result = src.take_while { |_h| true }
    assert_equal [{ v: 1 }, { v: 2 }], src
    refute_same src, result
    assert_same a, result[0]
  end

  def test_block_stops_at_first_falsy_and_iteration_ends
    # ブロックは最初に偽を返した要素まで呼ばれ、走査もそこで止まる
    seen = []
    [1, 2, 3, 4, 1].take_while { |x| seen << x; x < 3 }
    assert_equal [1, 2, 3], seen
    assert_equal [1, 2, 3], (1..).take_while { |x| x < 4 }
  end

  def test_only_nil_and_false_are_falsy
    # 偽になるのは nil と false だけで、0 や "" では打ち切らない
    assert_equal [1, 0, ""], [1, 0, "", nil, 2].take_while { |x| x }
  end

  def test_all_true_none_true_and_no_block
    # 全要素が真なら浅いコピー、先頭で偽なら []、ブロック無しは Enumerator
    src = [1, 2]
    all = src.take_while { |_x| true }
    assert_equal [1, 2], all
    refute_same src, all
    assert_equal [], [1, 2].take_while { |_x| false }
    assert_instance_of Enumerator, [1].take_while
  end

  def test_lazy_enumerator_defers_evaluation
    # Enumerator::Lazy なら後続の map も含めて first まで評価しない
    seen = []
    lazy = (1..).lazy.take_while { |x| seen << x; x < 4 }.map { |x| x * 10 }
    assert_instance_of Enumerator::Lazy, lazy
    assert_equal [], seen
    assert_equal [10, 20], lazy.first(2)
    assert_equal [1, 2], seen
  end

  def test_empty_input_returns_empty_array
    # 空配列は [] を返す
    assert_equal [], [].take_while { |_x| true }
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝わる
    assert_raises(IOError) { [1].take_while { |_x| raise IOError, "boom" } }
  end
end
