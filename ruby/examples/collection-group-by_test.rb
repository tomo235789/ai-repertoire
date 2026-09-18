# カード collection-group-by（Enumerable#group_by）の Contract を検証するテスト
require "minitest/autorun"

class CollectionGroupByTest < Minitest::Test
  def test_groups_keep_order_and_keys_are_in_first_seen_order
    # 各グループは出現順、キーはグループの初出順
    words = ["apple", "bob", "cat", "dove"]
    assert_equal({ 5 => ["apple"], 3 => ["bob", "cat"], 4 => ["dove"] }, words.group_by(&:size))
    assert_equal ["b", "a", "c"], ["b", "a", "b", "c", "a"].group_by { |x| x }.keys
  end

  def test_does_not_mutate_receiver_and_keeps_references
    # レシーバを変更せず、返り値はデフォルト値の無い新しい Hash で要素は同じ参照
    first = { t: "x" }
    src = [first, { t: "y" }]
    result = src.group_by { |h| h[:t] }
    assert_equal [{ t: "x" }, { t: "y" }], src
    assert_instance_of Hash, result
    assert_same first, result["x"][0]
    assert_nil result["missing"]
  end

  def test_is_eager_and_returns_enumerator_without_block
    # ブロック無しは Enumerator、ブロック付きは即時に全要素を読む
    assert_instance_of Enumerator, [1, 2].group_by
    seen = []
    enum = Enumerator.new { |y| 3.times { |i| seen << i; y << i } }
    enum.group_by(&:odd?)
    assert_equal [0, 1, 2], seen
  end

  def test_block_is_called_once_per_element_in_order
    # ブロックは各要素に 1 回ずつ先頭から呼ばれる
    seen = []
    [3, 1, 2].group_by { |x| seen << x; x.odd? }
    assert_equal [3, 1, 2], seen
  end

  def test_keys_are_compared_with_hash_and_eql
    # 1 と 1.0 は別グループ、nil もキーになる
    assert_equal({ 1 => [1], 1.0 => [1.0] }, [1, 1.0].group_by { |x| x })
    assert_equal({ nil => [nil], 1 => [1] }, [nil, 1].group_by { |x| x })
  end

  def test_empty_input_returns_empty_hash
    # 空配列は {} を返す
    assert_equal({}, [].group_by { |x| x })
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝わる
    assert_raises(IOError) { [1].group_by { |_x| raise IOError, "boom" } }
  end
end
