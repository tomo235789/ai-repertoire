# カード collection-zip（Array#zip）の Contract を検証するテスト
require "minitest/autorun"

class CollectionZipTest < Minitest::Test
  def test_pairs_by_position_in_order
    # 同じ位置の要素を順番どおり組にする
    assert_equal [[1, "a"], [2, "b"], [3, "c"]], [1, 2, 3].zip(["a", "b", "c"])
  end

  def test_does_not_mutate_inputs_and_keeps_references
    # レシーバも引数も変更せず、各組は要素の参照を共有する新しい配列
    a = { k: 1 }
    src = [a]
    other = ["x"]
    result = src.zip(other)
    assert_equal [{ k: 1 }], src
    assert_equal ["x"], other
    assert_same a, result[0][0]
  end

  def test_length_follows_receiver
    # レシーバの長さに合わせ、不足は nil、余りは切り捨て
    assert_equal [[1, "a"], [2, "b"], [3, nil]], [1, 2, 3].zip(["a", "b"])
    assert_equal [[1, "a"], [2, "b"]], [1, 2].zip(["a", "b", "c"])
  end

  def test_variadic_arguments
    # 引数は可変長で、無しなら 1 要素の配列に包む
    assert_equal [[1, 3, 5], [2, 4, 6]], [1, 2].zip([3, 4], [5, 6])
    assert_equal [[1], [2]], [1, 2].zip
  end

  def test_accepts_each_objects_and_rejects_others
    # each を持つ引数はレシーバの長さ分だけ読み、持たない値は TypeError
    assert_equal [[1, 1], [2, 2]], [1, 2].zip(1..)
    seen = []
    enum = Enumerator.new { |y| 5.times { |i| seen << i; y << i } }
    [1, 2].zip(enum)
    assert_equal [0, 1], seen
    assert_raises(TypeError) { [1, 2].zip(1) }
  end

  def test_with_block_yields_pairs_and_returns_nil
    # ブロック付きは各組を渡して nil を返す
    sums = []
    ret = [1, 2].zip([3, 4]) { |x, y| sums << x + y }
    assert_equal [4, 6], sums
    assert_nil ret
  end

  def test_empty_receiver_returns_empty_array
    # レシーバが空なら []。ブロック付きなら空でも nil
    assert_equal [], [].zip([1, 2])
    assert_nil([].zip([1, 2]) { |_pair| flunk "yield されない" })
  end
end
