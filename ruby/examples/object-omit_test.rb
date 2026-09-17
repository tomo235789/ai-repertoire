# カード object-omit の Contract を検証するテスト（Hash#except）
require "minitest/autorun"

class ObjectOmitTest < Minitest::Test
  def test_omits_given_keys
    # 指定したキーを除いたハッシュを返す
    user = { id: 1, name: "a", password: "x" }
    assert_equal({ id: 1, name: "a" }, user.except(:password))
    assert_equal({ id: 1 }, user.except(:password, :name))
  end

  def test_does_not_mutate_input_and_returns_shallow_copy
    # 入力ハッシュを変更せず、値は浅いコピー（ネストしたハッシュは同じオブジェクト）
    nested = { z: 1 }
    user = { id: 1, password: "x", nested: nested }
    result = user.except(:password)
    assert_equal({ id: 1, password: "x", nested: { z: 1 } }, user)
    assert_same nested, result[:nested]
  end

  def test_preserves_original_order
    # 残ったキーの順序は元のハッシュのまま
    h = { c: 3, a: 1, b: 2 }
    assert_equal [:c, :b], h.except(:a).keys
  end

  def test_missing_keys_are_ignored
    # 存在しないキーを指定しても無視される
    assert_equal({ a: 1 }, { a: 1 }.except(:missing))
  end

  def test_all_excluded_returns_empty_and_no_args_returns_copy
    # すべて除くと {}、引数無しなら同じ内容の別オブジェクト
    h = { a: 1, b: 2 }
    assert_equal({}, h.except(:a, :b))
    result = h.except
    assert_equal h, result
    refute_same h, result
  end

  def test_key_matching_uses_eql
    # キーの一致は eql? による。"a" と :a は別のキー
    assert_equal({ a: 2 }, { "a" => 1, a: 2 }.except("a"))
  end

  def test_default_is_not_inherited_but_compare_by_identity_is
    # default / default_proc は引き継がれず、compare_by_identity は引き継がれる
    with_default = Hash.new(0)
    with_default[:a] = 1
    assert_nil with_default.except(:a).default
    with_proc = Hash.new { |h, k| h[k] = [] }
    with_proc[:a] = 1
    assert_nil with_proc.except(:a).default_proc
    by_identity = { a: 1 }.compare_by_identity
    assert_predicate by_identity.except(:a), :compare_by_identity?
  end

  def test_array_argument_is_treated_as_single_key
    # Pitfalls: 配列を 1 つ渡すと配列そのものがキーとして扱われ何も除かれない。展開すれば除かれる
    h = { a: 1, b: 2 }
    keys = [:a]
    assert_equal({ a: 1, b: 2 }, h.except(keys))
    assert_equal({ b: 2 }, h.except(*keys))
  end

  def test_delete_mutates_original_and_returns_nil_for_missing
    # Alternatives: delete は元のハッシュを変え、存在しなければ nil を返す
    h = { a: 1, b: 2 }
    assert_nil h.delete(:missing)
    assert_equal 1, h.delete(:a)
    assert_equal({ b: 2 }, h)
  end
end
