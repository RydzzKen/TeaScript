import sys, os, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript.evaluator import Evaluator
from teascript.errors import RuntimeErrorTea


def run(src):
    Evaluator().run(Parser(Lexer(src).tokenize()).parse())


def capture(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(src)
    return buf.getvalue()


def expect_error(src):
    try:
        run(src)
    except RuntimeErrorTea as e:
        return e
    raise AssertionError(f"seharusnya error: {src}")


# --- list ---
def test_push_pop():
    assert capture("let xs = [1]\npush(xs, 2, 3)\nprint(xs)") == "[1, 2, 3]\n"
    assert capture("let xs = [1, 2]\nprint(pop(xs))\nprint(xs)") == "2\n[1]\n"


def test_push_error():
    e = expect_error('push("abc", 1)')
    assert "push()" in e.message
    assert e.line == 1


def test_pop_empty():
    e = expect_error("pop([])")
    assert "kosong" in e.message


# --- dict ---
def test_keys_values():
    assert capture('print(keys({a: 1, b: 2}))') == '["a", "b"]\n'
    assert capture('print(values({a: 1, b: 2}))') == "[1, 2]\n"


def test_keys_error():
    e = expect_error("keys([1])")
    assert "keys()" in e.message


# --- range ---
def test_range():
    assert capture("print(range(3))") == "[0, 1, 2]\n"
    assert capture("print(range(2, 5))") == "[2, 3, 4]\n"
    assert capture("print(range(0, 10, 3))") == "[0, 3, 6, 9]\n"
    assert capture("print(range(5, 0, -2))") == "[5, 3, 1]\n"


def test_range_error():
    e = expect_error("range(1.5)")
    assert "bulat" in e.message
    e = expect_error("range(0, 5, 0)")
    assert "step" in e.message


# --- type & includes ---
def test_type():
    assert capture("print(type(1), type(1.5), type(\"a\"), type(true), type(nil))") \
        == "number number string boolean nil\n"
    assert capture("print(type([1]), type({a: 1}), type(print))") == "list dict function\n"


def test_includes():
    assert capture('print(includes([1, 2], 2))') == "true\n"
    assert capture('print(includes("halo", "ha"))') == "true\n"
    assert capture('print(includes({a: 1}, "b"))') == "false\n"


# --- string ---
def test_string_functions():
    assert capture('print(upper("abc"), lower("ABC"), trim("  x  "))') == "ABC abc x\n"
    assert capture('print(split("a,b,c", ","))') == '["a", "b", "c"]\n'
    assert capture('print(split("abc", ""))') == '["a", "b", "c"]\n'
    assert capture('print(join(["a", "b"], "-"))') == "a-b\n"
    assert capture('print(join([1, 2], ", "))') == "1, 2\n"


def test_string_function_error():
    e = expect_error("upper(5)")
    assert "upper()" in e.message
    assert e.line == 1  # posisi pemanggilan dilengkapi ke error
    e = expect_error('split(1, ",")')
    assert "split()" in e.message


# --- angka ---
def test_abs_min_max():
    assert capture("print(abs(-5), abs(2.5))") == "5 2.5\n"
    assert capture("print(min(3, 1, 2), max(3, 1, 2))") == "1 3\n"
    assert capture("print(min([4, 2, 9]), max([4, 2, 9]))") == "2 9\n"


def test_min_max_error():
    e = expect_error('min("a")')
    assert "min()" in e.message
    e = expect_error("min()")
    assert "minimal" in e.message
    e = expect_error("abs(true)")
    assert "abs()" in e.message
