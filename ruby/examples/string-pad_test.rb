# カード string-pad の Contract を検証するテスト（String#center）
require "minitest/autorun"

class StringPadTest < Minitest::Test
  def test_pads_both_sides
    # 左右に padstr を詰めて指定幅にする
    assert_equal "  abc   ", "abc".center(8)
    assert_equal "**abc***", "abc".center(8, "*")
    assert_equal "abc***", "abc".ljust(6, "*")
    assert_equal "***abc", "abc".rjust(6, "*")
  end

  def test_returns_new_string_without_mutating
    # 元の文字列は変わらず、幅以下でも同じオブジェクトは返さない
    s = "abc"
    result = s.center(8)
    assert_equal "abc", s
    assert_equal "abc", s.center(3)
    refute_same s, s.center(3)
    refute_same s, result
  end

  def test_odd_remainder_goes_to_right_regardless_of_width_parity
    # 余りが奇数なら右側が 1 文字多い。幅の偶奇に依存しない
    assert_equal "abc ", "abc".center(4)
    assert_equal " ab  ", "ab".center(5)
    assert_equal " a  ", "a".center(4)
    assert_equal "  abc  ", "abc".center(7)
  end

  def test_width_at_or_below_length_returns_same_content
    # 幅が長さ以下（0、負数を含む）なら切り詰めずそのまま
    assert_equal "abc", "abc".center(2)
    assert_equal "abc", "abc".center(0)
    assert_equal "abc", "abc".center(-1)
  end

  def test_multi_char_padstr_repeats_from_each_edge
    # 複数文字の padstr は左右それぞれの端から繰り返し、端数は切り落とす
    assert_equal "_-abc_-_", "abc".center(8, "_-")
    assert_equal "_-_abc_-_", "abc".center(9, "_-")
    assert_equal "abc_-_-_", "abc".ljust(8, "_-")
    assert_equal "_-_-_abc", "abc".rjust(8, "_-")
  end

  def test_empty_string_is_filled_with_padstr
    # 空文字は padstr だけで埋まる
    assert_equal "xxx", "".center(3, "x")
  end

  def test_invalid_arguments
    # 空の padstr は ArgumentError、型が違えば TypeError、Float の幅は切り捨て
    assert_raises(ArgumentError) { "abc".center(8, "") }
    assert_raises(TypeError) { "abc".center(8, 1) }
    assert_raises(TypeError) { "abc".center("8") }
    assert_raises(TypeError) { "abc".center(nil) }
    assert_equal "  abc   ", "abc".center(8.9)
  end

  def test_incompatible_encodings_raise
    # padstr と自身のエンコーディングが互換でなければ Encoding::CompatibilityError。埋め込み不要な幅でも投げる
    sjis = "日".encode("Shift_JIS")
    assert_raises(Encoding::CompatibilityError) { "日本".center(8, sjis) }
    assert_raises(Encoding::CompatibilityError) { "日本".center(1, sjis) }
    assert_equal 8, "abc".center(8, sjis).length
  end

  def test_counts_codepoints
    # 長さはコードポイント単位。全角も 1、結合文字や ZWJ 絵文字列は複数
    assert_equal "**日本**", "日本".center(6, "*")
    assert_equal "*😀*", "😀".center(3, "*")
    assert_equal "*é*", "é".center(4, "*")
    assert_equal 8, "abc".center(8, "日").length
    assert_equal "日日abc日日日", "abc".center(8, "日")
  end

  def test_zero_padding_alternatives
    # Alternatives: 負数のゼロ埋めは rjust だと符号が崩れる。format を使う
    assert_equal "005", "5".rjust(3, "0")
    assert_equal "0-5", "-5".rjust(3, "0")
    assert_equal "-05", format("%03d", -5)
    assert_equal "abc     |", format("%-8s|", "abc")
    assert_equal "     abc|", format("%8s|", "abc")
  end
end
