import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.token import NUMBER, IDENT, KEYWORD, OP, STRING, INTERP, EOF
from teascript.errors import SyntaxErrorTea


def test_numbers():
    toks = Lexer("42 3.14").tokenize()
    assert toks[0].type == NUMBER and toks[0].value == 42
    assert toks[1].type == NUMBER and toks[1].value == 3.14
    assert toks[2].type == EOF


def test_keywords():
    toks = Lexer("let if while fn return").tokenize()
    assert all(t.type == KEYWORD for t in toks[:-1])


def test_line_numbers():
    toks = Lexer("a\nb\nc").tokenize()
    assert toks[0].line == 1
    assert toks[1].line == 2
    assert toks[2].line == 3


def test_string():
    toks = Lexer('"halo"').tokenize()
    assert toks[0].value == "halo"


def test_comment():
    toks = Lexer("1 // komentar\n2").tokenize()
    assert toks[0].value == 1
    assert toks[1].value == 2


def test_unterminated_string():
    try:
        Lexer('"abc').tokenize()
        assert False, "harusnya error"
    except SyntaxErrorTea as e:
        assert "string tidak ditutup" in e.message
        assert e.line == 1


def test_compound_ops():
    toks = Lexer("+= -= *= /= %=").tokenize()
    assert [t.value for t in toks[:-1]] == ["+=", "-=", "*=", "/=", "%="]
    assert all(t.type == OP for t in toks[:-1])


def test_ternary_op():
    toks = Lexer("a ? b : c").tokenize()
    assert toks[1].type == OP and toks[1].value == "?"
    assert toks[2].type == IDENT and toks[2].value == "b"


def test_new_keywords():
    toks = Lexer("for in break continue").tokenize()
    assert all(t.type == KEYWORD for t in toks[:-1])
    # 'in' tidak lagi jadi identifier biasa
    assert Lexer("in").tokenize()[0].type == KEYWORD


def test_interpolation_token():
    toks = Lexer('"Halo, ${nama}!"').tokenize()
    assert toks[0].type == INTERP
    parts = toks[0].value
    assert parts[0] == ("text", "Halo, ")
    assert parts[1][0] == "expr" and parts[1][1] == "nama"
    assert parts[2] == ("text", "!")


def test_string_without_interp_stays_string():
    # $ tanpa { tidak memicu interpolasi
    toks = Lexer('"harga $5"').tokenize()
    assert toks[0].type == STRING and toks[0].value == "harga $5"


def test_escaped_dollar():
    toks = Lexer('"\\${x}"').tokenize()
    assert toks[0].type == STRING and toks[0].value == "${x}"


def test_interpolation_positions():
    toks = Lexer('let s = "a ${1 + 1} b"').tokenize()
    expr_part = next(p for p in toks[3].value if p[0] == "expr")
    _, src, line, col = expr_part
    assert src == "1 + 1"
    assert line == 1
    # 'let s = "a ${' → kolom 14 adalah karakter pertama ekspresi
    assert col == 14


def test_unclosed_interpolation():
    try:
        Lexer('"${x').tokenize()
        assert False, "harusnya error"
    except SyntaxErrorTea as e:
        assert "${" in e.message


def test_empty_interpolation():
    try:
        Lexer('"${ }"').tokenize()
        assert False, "harusnya error"
    except SyntaxErrorTea as e:
        assert "kosong" in e.message