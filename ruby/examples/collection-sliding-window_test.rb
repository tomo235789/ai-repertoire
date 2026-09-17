# カード collection-sliding-window（Enumerable#each_cons）の Contract を検証するテスト
require "minitest/autorun"

class CollectionSlidingWindowTest < Minitest::Test
  def test_windows_shift_by_one_in_order
    # 窓は 1 つずつずれ、窓の中も元の並び順
    assert_equal [[1, 2, 3], [2, 3, 4], [3, 4, 5]], [1, 2, 3, 4, 5].each_cons(3).to_a
    assert_equal [1, 1, 1, 1], [1, 2, 3, 4, 5].each_cons(2).map { |a, b| b - a }
  end

  def test_does_not_mutate_receiver_and_each_window_is_new_array
    # レシーバを変更せず、各窓は別オブジェクトの新しい配列で要素は同じ参照
    a = { k: 1 }
    src = [a, { k: 2 }, { k: 3 }]
    windows = src.each_cons(2).to_a
    assert_equal [{ k: 1 }, { k: 2 }, { k: 3 }], src
    assert_same a, windows[0][0]
    refute_same windows[0], windows[1]
  end

  def test_without_block_returns_enumerator_and_reads_lazily
    # ブロック無しは Enumerator で、必要な分だけ入力を読み進める
    assert_instance_of Enumerator, [1, 2].each_cons(2)
    seen = []
    enum = Enumerator.new { |y| 10.times { |i| seen << i; y << i } }
    assert_equal [[0, 1, 2], [1, 2, 3]], enum.each_cons(3).first(2)
    assert_equal [0, 1, 2, 3], seen
  end

  def test_with_block_returns_receiver
    # ブロック付きはレシーバ自身を返す
    src = [1, 2, 3]
    assert_same src, src.each_cons(2) { |_w| }
  end

  def test_drops_trailing_partial_windows
    # n に満たない末尾の窓は出さず、要素数が n 未満なら空
    assert_equal [[1, 2, 3]], [1, 2, 3].each_cons(3).to_a
    assert_equal [], [1, 2].each_cons(3).to_a
  end

  def test_step_can_be_emulated_with_each_slice
    # step 相当は each_slice との組み合わせで代用できる
    assert_equal [[1, 2, 3], [3, 4, 5]], [1, 2, 3, 4, 5].each_cons(3).each_slice(2).map(&:first)
  end

  def test_empty_input_yields_nothing
    # 空配列は何も yield しない
    assert_equal [], [].each_cons(2).to_a
  end

  def test_invalid_n_raises
    # n が 0 以下なら ArgumentError、整数に変換できなければ TypeError、小数は切り捨て
    assert_raises(ArgumentError) { [1].each_cons(0).to_a }
    assert_raises(ArgumentError) { [1].each_cons(-1).to_a }
    assert_raises(TypeError) { [1].each_cons("2").to_a }
    assert_equal [[1], [2]], [1, 2].each_cons(1.5).to_a
  end
end
