# カード collection-flatten（Array#flatten）の Contract を検証するテスト
require "minitest/autorun"

class CollectionFlattenTest < Minitest::Test
  def test_flattens_depth_first_in_order
    # 深さ優先で左から順に展開する
    assert_equal [1, 2, 3, 4], [1, [2, [3, [4]]]].flatten
    assert_equal [1, 2, [3, [4]]], [1, [2, [3, [4]]]].flatten(1)
  end

  def test_does_not_mutate_receiver_and_keeps_deeper_references
    # レシーバを変更せず、level より深い配列は同じ参照
    inner = [3]
    src = [[1, inner]]
    result = src.flatten(1)
    assert_equal [[1, [3]]], src
    refute_same src, result
    assert_same inner, result[1]
  end

  def test_level_nil_negative_and_zero
    # 省略・nil・負数は全段、0 は展開せず浅いコピー
    assert_equal [1, 2, 3], [1, [2, [3]]].flatten(nil)
    assert_equal [1, 2, 3], [1, [2, [3]]].flatten(-1)
    src = [1, [2]]
    copy = src.flatten(0)
    assert_equal [1, [2]], copy
    refute_same src, copy
  end

  def test_only_arrays_and_to_ary_objects_are_flattened
    # 配列と to_ary を持つオブジェクトだけ展開し、文字列や Hash は残す
    assert_equal ["ab", "cd", { a: 1 }], ["ab", ["cd"], [{ a: 1 }]].flatten
    obj = Object.new
    def obj.to_ary
      [9, 9]
    end
    assert_equal [1, 9, 9], [1, obj].flatten
  end

  def test_empty_inputs_return_empty_array
    # 空配列と空配列だけの配列は []
    assert_equal [], [].flatten
    assert_equal [], [[], [[]]].flatten
  end

  def test_recursive_array_raises_unless_level_is_given
    # 再帰的な配列は全段展開で ArgumentError、level 指定なら展開できる
    rec = [1]
    rec << rec
    assert_raises(ArgumentError) { rec.flatten }
    assert_equal 3, rec.flatten(1).size
  end

  def test_invalid_level_raises_and_float_is_truncated
    # 整数に変換できない level は TypeError、小数は切り捨て
    assert_raises(TypeError) { [1, [2]].flatten("1") }
    assert_equal [1, 2, [3]], [1, [2, [3]]].flatten(1.9)
  end

  def test_bang_version_returns_nil_when_unchanged
    # flatten! は変更が無ければ nil
    src = [1, [2]]
    assert_same src, src.flatten!
    assert_equal [1, 2], src
    assert_nil [1, 2].flatten!
  end
end
