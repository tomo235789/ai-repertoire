# カード collection-chunk（Enumerable#each_slice）の Contract を検証するテスト
require "minitest/autorun"

class CollectionChunkTest < Minitest::Test
  def test_keeps_order_and_last_slice_is_shorter
    # 順序を保ったまま n ごとに分割し、最後は短くなる
    assert_equal [[1, 2], [3, 4], [5]], [1, 2, 3, 4, 5].each_slice(2).to_a
    assert_equal [[1, 2]], [1, 2].each_slice(5).to_a
  end

  def test_does_not_mutate_receiver_and_keeps_references
    # レシーバを変更せず、各小配列は要素の参照を共有する新しい配列
    a = { k: 1 }
    src = [a, { k: 2 }, { k: 3 }]
    result = src.each_slice(2).to_a
    assert_equal [{ k: 1 }, { k: 2 }, { k: 3 }], src
    assert_same a, result[0][0]
    refute_same src, result[0]
  end

  def test_without_block_returns_enumerator_and_reads_lazily
    # ブロック無しは Enumerator を返し、必要な分だけ入力を読み進める
    assert_instance_of Enumerator, [1, 2, 3].each_slice(2)
    seen = []
    enum = Enumerator.new { |y| 5.times { |i| seen << i; y << i } }
    assert_equal [[0, 1]], enum.each_slice(2).first(1)
    assert_equal [0, 1], seen
  end

  def test_with_block_returns_receiver
    # ブロック付きはレシーバ自身を返す
    src = [1, 2, 3]
    yielded = []
    ret = src.each_slice(2) { |s| yielded << s }
    assert_same src, ret
    assert_equal [[1, 2], [3]], yielded
  end

  def test_empty_input_yields_nothing
    # 空配列は何も yield しない
    assert_equal [], [].each_slice(3).to_a
  end

  def test_invalid_n_raises
    # n が 0 以下なら ArgumentError、整数に変換できなければ TypeError、小数は切り捨て
    assert_raises(ArgumentError) { [1, 2].each_slice(0).to_a }
    assert_raises(ArgumentError) { [1, 2].each_slice(-1).to_a }
    assert_raises(TypeError) { [1, 2].each_slice("2").to_a }
    assert_equal [[1], [2], [3]], [1, 2, 3].each_slice(1.5).to_a
  end
end
