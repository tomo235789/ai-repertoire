# カード object-invert の Contract を検証するテスト（Hash#invert）
require "minitest/autorun"

class ObjectInvertTest < Minitest::Test
  def test_swaps_keys_and_values
    # キーと値を入れ替える
    code_to_name = { 1 => "red", 2 => "blue" }
    assert_equal({ "red" => 1, "blue" => 2 }, code_to_name.invert)
  end

  def test_does_not_mutate_input
    # 入力ハッシュを変更せず、新しいハッシュを返す
    h = { 1 => "red" }
    result = h.invert
    assert_equal({ 1 => "red" }, h)
    refute_same h, result
  end

  def test_keeps_types_and_insertion_order
    # 型はそのまま（文字列化しない）で、順序は挿入順
    inverted = { "b" => 2, :a => 1 }.invert
    assert_equal [2, 1], inverted.keys
    assert_equal ["b", :a], inverted.values
  end

  def test_duplicate_values_keep_last_key_at_first_position
    # 値が重複したら最後のキーが残り、位置は最初に出現した場所
    assert_equal({ 1 => :a }, { b: 1, a: 1 }.invert)
    assert_equal({ 1 => :c, 2 => :b }, { a: 1, b: 2, c: 1 }.invert)
    assert_equal [1, 2], { a: 1, b: 2, c: 1 }.invert.keys
  end

  def test_integer_and_float_are_distinct_keys
    # 1 と 1.0 は別のキーになる（eql? で判定）
    assert_equal({ 1 => :a, 1.0 => :b }, { a: 1, b: 1.0 }.invert)
    assert_equal 2, { a: 1, b: 1.0 }.invert.size
    assert_equal 2, { a: 1, b: true }.invert.size
  end

  def test_empty_hash_returns_empty
    # 空のハッシュは {} を返す
    assert_equal({}, {}.invert)
  end

  def test_nil_and_mutable_values_become_keys_without_error
    # nil や配列の値も例外無くキーになる
    assert_equal({ nil => :a }, { a: nil }.invert)
    assert_equal({ [1, 2] => :a }, { a: [1, 2] }.invert)
  end

  def test_default_and_compare_by_identity_are_not_inherited
    # default / compare_by_identity は返り値に引き継がれない
    with_default = Hash.new(0)
    with_default[:a] = 1
    assert_nil with_default.invert.default
    by_identity = { a: 1 }.compare_by_identity
    refute_predicate by_identity.invert, :compare_by_identity?
  end

  def test_key_and_rassoc_look_up_first_match
    # Alternatives: key は最初に一致したキー、rassoc は [key, value] の組。無ければ nil
    h = { a: 1, b: 2, c: 1 }
    assert_equal :a, h.key(1)
    assert_nil h.key(3)
    assert_equal [:b, 2], h.rassoc(2)
    assert_equal({ 1 => [:a, :c], 2 => [:b] }, h.group_by { |_k, v| v }.transform_values { |pairs| pairs.map(&:first) })
  end

  def test_mutated_array_key_needs_rehash
    # Pitfalls: 配列キーの中身を変えると [] で引けなくなり、rehash で引けるようになる
    arr = [1, 2]
    inverted = { a: arr }.invert
    arr << 3
    assert_nil inverted[[1, 2, 3]]
    inverted.rehash
    assert_equal :a, inverted[[1, 2, 3]]
  end
end
