# カード collection-partition（Enumerable#partition）の Contract を検証するテスト
require "minitest/autorun"

class CollectionPartitionTest < Minitest::Test
  def test_truthy_first_and_keeps_order
    # [真, 偽] の順で、両方とも元の並び順
    assert_equal [[2, 4], [1, 3, 5]], [1, 2, 3, 4, 5].partition(&:even?)
  end

  def test_does_not_mutate_receiver_and_keeps_references
    # レシーバを変更せず、返り値は要素の参照を共有する新しい配列 2 つ
    a = { ok: true }
    src = [a, { ok: false }]
    trues, falses = src.partition { |h| h[:ok] }
    assert_equal [{ ok: true }, { ok: false }], src
    assert_same a, trues[0]
    assert_equal [{ ok: false }], falses
  end

  def test_returns_enumerator_without_block
    # ブロック無しは Enumerator を返す
    assert_instance_of Enumerator, [1].partition
  end

  def test_block_is_called_once_per_element_in_order
    # ブロックは各要素に 1 回ずつ先頭から呼ばれる
    seen = []
    [3, 1, 2].partition { |x| seen << x; true }
    assert_equal [3, 1, 2], seen
  end

  def test_only_nil_and_false_are_falsy
    # 偽になるのは nil と false だけで、0 や "" は真側
    assert_equal [[0, "", 1], [nil, false]], [0, "", nil, false, 1].partition { |x| x }
  end

  def test_empty_input_returns_two_empty_arrays
    # 空配列は [[], []] を返す
    assert_equal [[], []], [].partition(&:even?)
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝わる
    assert_raises(IOError) { [1].partition { |_x| raise IOError, "boom" } }
  end
end
