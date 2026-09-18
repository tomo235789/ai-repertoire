# カード object-map-values の Contract を検証するテスト（Hash#transform_values）
require "minitest/autorun"

class ObjectMapValuesTest < Minitest::Test
  def test_maps_each_value_keeping_keys
    # キーはそのままに各値を変換する
    scores = { alice: [80, 90], bob: [70] }
    assert_equal({ alice: 2, bob: 1 }, scores.transform_values { |list| list.length })
    assert_equal({ alice: 170, bob: 70 }, scores.transform_values(&:sum))
  end

  def test_preserves_key_order
    # キーの順序を保持する
    h = { c: 3, a: 1, b: 2 }
    assert_equal [:c, :a, :b], h.transform_values { |v| v * 2 }.keys
  end

  def test_does_not_mutate_input_and_keeps_returned_objects
    # 入力を変更せず、ブロックが返したオブジェクトがそのまま入る
    list = [1]
    h = { a: list }
    result = h.transform_values { |v| v }
    assert_equal({ a: [1] }, h)
    refute_same h, result
    assert_same list, result[:a]
  end

  def test_block_is_called_once_per_key_in_order_with_value_only
    # ブロックは各キーにつき 1 回、挿入順に、値だけを引数に呼ばれる
    calls = []
    { b: 1, a: 2 }.transform_values { |*args| calls << args; args.first }
    assert_equal [[1], [2]], calls
  end

  def test_empty_hash_returns_empty
    # 空のハッシュは {} を返す
    assert_equal({}, {}.transform_values { |v| v * 2 })
  end

  def test_default_is_not_inherited_but_compare_by_identity_is
    # default は引き継がれず、compare_by_identity は引き継がれる
    with_default = Hash.new(0)
    with_default[:a] = 1
    assert_nil with_default.transform_values { |v| v }.default
    by_identity = { a: 1 }.compare_by_identity
    assert_predicate by_identity.transform_values { |v| v }, :compare_by_identity?
  end

  def test_without_block_returns_enumerator
    # ブロック無しなら Enumerator を返す
    enum = { a: 1, b: 2 }.transform_values
    assert_kind_of Enumerator, enum
    assert_equal({ a: 2, b: 4 }, enum.each { |v| v * 2 })
  end

  def test_block_exception_propagates
    # ブロックが投げた例外はそのまま伝播する
    assert_raises(ArgumentError) { { a: 1 }.transform_values { raise ArgumentError, "boom" } }
  end

  def test_bang_version_mutates_and_to_h_changes_keys_too
    # Alternatives: transform_values! は self を書き換え、to_h { } はキーも変えられる
    h = { a: 1 }
    assert_same h, h.transform_values! { |v| v + 1 }
    assert_equal({ a: 2 }, h)
    assert_equal({ "a" => 2, "b" => 4 }, { a: 1, b: 2 }.to_h { |k, v| [k.to_s, v * 2] })
  end

  def test_map_returns_array_of_pairs
    # Pitfalls: Hash#map は配列の配列を返す。to_h でハッシュに戻す
    pairs = { a: 1 }.map { |k, v| [k, v * 2] }
    assert_equal [[:a, 2]], pairs
    assert_equal({ a: 2 }, pairs.to_h)
  end
end
