import sys, os, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript.evaluator import Evaluator
from teascript.errors import NameErrorTea, RuntimeErrorTea


def run(src):
    tokens = Lexer(src).tokenize()
    program = Parser(tokens).parse()
    Evaluator().run(program)


def capture(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(src)
    return buf.getvalue()


def test_arithmetic():
    assert capture("print(1 + 2 * 3)") == "7\n"


def test_string_concat():
    assert capture('print("a" + "b")') == "ab\n"


def test_comparison():
    assert capture("print(1 < 2)") == "true\n"
    assert capture("print(2 == 3)") == "false\n"


def test_logic():
    assert capture("print(true and false)") == "false\n"
    assert capture("print(true or false)") == "true\n"
    assert capture("print(not true)") == "false\n"


def test_if_else():
    assert capture("if 1 < 2 { print(1) } else { print(2) }") == "1\n"


def test_while():
    assert capture("let i = 0\nwhile i < 3 { print(i)\ni = i + 1 }") == "0\n1\n2\n"


def test_fn_recursive():
    src = """
    fn fib(n) {
      if n < 2 { return n }
      return fib(n - 1) + fib(n - 2)
    }
    print(fib(6))
    """
    assert capture(src) == "8\n"


def test_function_local_scope():
    src = """
    let x = 10
    fn f() { let x = 99\nreturn x }
    print(f())
    print(x)
    """
    assert capture(src) == "99\n10\n"


def test_list():
    assert capture("let xs = [1, 2, 3]\nprint(xs[1])") == "2\n"
    assert capture("let xs = [1, 2]\nxs[0] = 9\nprint(xs[0])") == "9\n"


def test_dict():
    assert capture('let d = {nama: "budi"}\nprint(d["nama"])') == "budi\n"
    assert capture('let d = {a: 1}\nd["b"] = 2\nprint(d["b"])') == "2\n"


def test_len():
    assert capture("print(len([1,2,3]))") == "3\n"
    assert capture('print(len("halo"))') == "4\n"


def test_str_num():
    assert capture('print(str(42))') == "42\n"
    assert capture('print(num("7"))') == "7\n"


def test_name_error():
    try:
        run("print(umur)")
        assert False
    except NameErrorTea as e:
        assert "umur" in e.message
        assert e.line == 1


def test_division_by_zero():
    try:
        run("print(1 / 0)")
        assert False
    except RuntimeErrorTea as e:
        assert "nol" in e.message


def test_syntax_error_line():
    from teascript.errors import SyntaxErrorTea
    try:
        run("let x = \nlet y = 2")
        assert False
    except SyntaxErrorTea as e:
        assert e.line is not None


def test_for_in_list():
    assert capture("for x in [1, 2, 3] { print(x) }") == "1\n2\n3\n"


def test_for_in_string():
    assert capture('for c in "abc" { print(c) }') == "a\nb\nc\n"


def test_for_in_dict_keys():
    assert capture('for k in {a: 1, b: 2} { print(k) }') == "a\nb\n"


def test_for_in_range():
    assert capture("for i in range(3) { print(i) }") == "0\n1\n2\n"


def test_for_in_loop_var_berganti():
    src = """
    let hasil = ""
    for c in "abc" { hasil = hasil + c }
    print(hasil)
    """
    assert capture(src) == "abc\n"


def test_while_break_continue():
    src = """
    let i = 0
    while i < 10 {
      i += 1
      if i == 3 { continue }
      if i == 5 { break }
      print(i)
    }
    """
    assert capture(src) == "1\n2\n4\n"


def test_for_break_continue():
    src = """
    for i in range(10) {
      if i == 2 { continue }
      if i == 4 { break }
      print(i)
    }
    """
    assert capture(src) == "0\n1\n3\n"


def test_nested_loop_break_hanya_menghenti_loop_dalam():
    src = """
    for i in range(2) {
      for j in range(10) {
        if j == 1 { break }
        print(i, j)
      }
    }
    """
    assert capture(src) == "0 0\n1 0\n"


def test_break_di_luar_loop():
    from teascript.errors import RuntimeErrorTea
    try:
        run("break")
        assert False
    except RuntimeErrorTea as e:
        assert "break" in e.message
        assert e.line == 1


def test_continue_di_luar_loop():
    from teascript.errors import RuntimeErrorTea
    try:
        run("fn f() { continue }\nf()")
        assert False
    except RuntimeErrorTea as e:
        assert "continue" in e.message


def test_ternary():
    assert capture('print(1 < 2 ? "iya" : "tidak")') == "iya\n"
    assert capture('print(1 > 2 ? "iya" : "tidak")') == "tidak\n"


def test_compound_assign():
    # '/' selalu menghasilkan desimal (gaya Python): 26 / 2 -> 13.0
    assert capture("let x = 10\nx += 5\nx *= 2\nx -= 4\nx /= 2\nprint(x)") == "13.0\n"
    assert capture("let xs = [1, 2]\nxs[0] += 10\nprint(xs[0])") == "11\n"


def test_string_interpolation():
    assert capture('let n = "Ken"\nprint("Halo, ${n}!")') == "Halo, Ken!\n"


def test_interpolation_ekspresi():
    assert capture('print("1+1=${1 + 1}, list=${[1,2]}")') == "1+1=2, list=[1, 2]\n"


def test_interpolation_dalam_interpolasi_fungsi():
    assert capture('fn gt(n) { return n * 2 }\nprint("hasil: ${gt(21)}")') == "hasil: 42\n"


def test_interpolation_string_dalam_ekspresi():
    # string literal di dalam ${...} tidak menutup string luar
    assert capture('let x = 5\nprint("${x > 3 ? "gede" : "kecil"}")') == "gede\n"


def test_interpolation_error_posisi():
    from teascript.errors import SyntaxErrorTea
    try:
        run('print("${1 + }")')
        assert False
    except SyntaxErrorTea as e:
        assert e.line == 1


def test_slice_list():
    assert capture("let xs = [1, 2, 3, 4, 5]\nprint(xs[1:3])") == "[2, 3]\n"
    assert capture("let xs = [1, 2, 3]\nprint(xs[:2])") == "[1, 2]\n"
    assert capture("let xs = [1, 2, 3]\nprint(xs[1:])") == "[2, 3]\n"
    assert capture("let xs = [1, 2, 3]\nprint(xs[:])") == "[1, 2, 3]\n"


def test_slice_string():
    assert capture('let s = "Hello World"\nprint(s[0:5])') == "Hello\n"
    assert capture('let s = "Hello World"\nprint(s[6:])') == "World\n"


def test_slice_negatif_dan_clamp():
    assert capture("let xs = [1, 2, 3, 4]\nprint(xs[-2:])") == "[3, 4]\n"
    assert capture("let xs = [1, 2, 3]\nprint(xs[0:99])") == "[1, 2, 3]\n"
    assert capture("let xs = [1, 2, 3]\nprint(xs[5:2])") == "[]\n"


def test_slice_error():
    from teascript.errors import RuntimeErrorTea
    try:
        run("print({a: 1}[0:1])")
        assert False
    except RuntimeErrorTea as e:
        assert "slice" in e.message
        assert e.line == 1


def test_operator_in():
    assert capture("print(2 in [1, 2, 3])") == "true\n"
    assert capture("print(9 in [1, 2, 3])") == "false\n"
    assert capture('print("ha" in "halo")') == "true\n"
    assert capture('print("a" in {a: 1})') == "true\n"
    assert capture('print("b" not in {a: 1})') == "true\n"
    assert capture("print(not (5 in [1, 2]))") == "true\n"


def test_in_list_bandkan_nilai_bool():
    # 1 dan true tidak boleh dianggap sama
    assert capture("print(true in [1])") == "false\n"
    assert capture("print(1 in [true])") == "false\n"