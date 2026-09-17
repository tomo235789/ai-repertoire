# カード object-pick（Hash#slice）の Contract を検証するテスト
require "minitest/autorun"

class ObjectPickTest < Minitest::Test
  def test_does_not_mutate_receiver_and_values_are_shared
    # レシーバを変更せず、返り値は値の参照を共有する新しい Hash
    tags = ["x"]
    src = { id: 1, tags: tags, pw: "x" }
    result = src.slice(:id, :tags)
    assert_equal({ id: 1, tags: ["x"], pw: "x" }, src)
    refute_same src, result
    assert_same tags, result[:tags]
  end

  def test_ignores_missing_keys_and_keeps_nil_values
    # 存在しないキーは無視し、値が nil のキーは含める
    assert_equal({ id: 1 }, { id: 1, name: "a" }.slice(:id, :missing))
    assert_equal({ a: nil }, { a: nil }.slice(:a))
  end

  def test_result_keys_follow_argument_order_and_dedupe
    # 返り値のキーは引数の順で、重複は 1 つにまとまる
    assert_equal [:c, :a], { a: 1, b: 2, c: 3 }.slice(:c, :a).keys
    assert_equal({ a: 1 }, { a: 1, b: 2 }.slice(:a, :a))
  end

  def test_keys_are_compared_like_the_receiver
    # キーの比較は元の Hash と同じで、1 と 1.0・"a" と :a は別、compare_by_identity なら同一性
    assert_equal({}, { 1 => :int }.slice(1.0))
    assert_equal({}, { "a" => 1 }.slice(:a))
    ident = {}.compare_by_identity
    ident["a"] = 1
    assert_equal({}, ident.slice("a".dup))
    assert_predicate ident.slice, :compare_by_identity?
  end

  def test_returns_empty_hash_when_nothing_matches
    # 引数無し・該当無しは {}
    assert_equal({}, { a: 1 }.slice)
    assert_equal({}, {}.slice(:a))
  end

  def test_default_value_is_not_carried_over
    # デフォルト値・デフォルトブロックは引き継がれない
    with_default = Hash.new(0)
    with_default[:a] = 1
    assert_nil with_default.slice(:a)[:zz]
    with_proc = Hash.new { |_h, _k| 0 }
    with_proc[:a] = 1
    assert_nil with_proc.slice(:a).default_proc
  end

  def test_array_argument_is_a_single_key_and_bang_version_does_not_exist
    # 配列を splat せずに渡すと 1 つのキー扱いで {}、slice! は素の Ruby には無い
    assert_equal({}, { a: 1, b: 2 }.slice([:a, :b]))
    assert_equal({ a: 1, b: 2 }, { a: 1, b: 2 }.slice(*[:a, :b]))
    assert_raises(NoMethodError) { { a: 1 }.slice!(:a) }
  end
end
