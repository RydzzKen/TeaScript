import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript import ast_nodes as ast
from teascript.errors import SyntaxErrorTea


def parse(src):
    return Parser(Lexer(src).tokenize()).parse()


def test_let():
    p = parse("let x = 1")
    assert isinstance(p.statements[0], ast.Let)
    assert p.statements[0].name == "x"


def test_precedence():
    p = parse("1 + 2 * 3")
    expr = p.statements[0].expr
    assert isinstance(expr, ast.Binary) and expr.op == "+"
    assert isinstance(expr.right, ast.Binary) and expr.right.op == "*"


def test_precedence_paren():
    p = parse("(1 + 2) * 3")
    expr = p.statements[0].expr
    assert expr.op == "*"
    assert expr.left.op == "+"


def test_if_else():
    p = parse("if x { 1 } else { 2 }")
    stmt = p.statements[0]
    assert isinstance(stmt, ast.If)
    assert len(stmt.then_body) == 1
    assert len(stmt.else_body) == 1


def test_while():
    p = parse("while x < 3 { x = x + 1 }")
    assert isinstance(p.statements[0], ast.While)


def test_fn():
    p = parse("fn add(a, b) { return a + b }")
    stmt = p.statements[0]
    assert stmt.name == "add"
    assert stmt.params == ["a", "b"]


def test_missing_brace():
    try:
        parse("if x { 1")
        assert False
    except SyntaxErrorTea as e:
        assert e.line == 1


def test_ternary():
    p = parse("x > 0 ? 1 : -1")
    expr = p.statements[0].expr
    assert isinstance(expr, ast.Ternary)
    assert expr.condition.op == ">"


def test_ternary_right_assoc():
    # a ? b : c ? d : e  →  a ? b : (c ? d : e)
    expr = parse("a ? b : c ? d : e").statements[0].expr
    assert isinstance(expr.otherwise, ast.Ternary)


def test_for_in():
    stmt = parse("for x in xs { print(x) }").statements[0]
    assert isinstance(stmt, ast.ForIn)
    assert stmt.name == "x"
    assert isinstance(stmt.iterable, ast.Ident)
    assert len(stmt.body) == 1


def test_break_continue():
    p = parse("while true { break\ncontinue }")
    body = p.statements[0].body
    assert isinstance(body[0], ast.Break)
    assert isinstance(body[1], ast.Continue)


def test_compound_assign():
    stmt = parse("x += 1").statements[0]
    assert isinstance(stmt, ast.Assign)
    assert isinstance(stmt.value, ast.Binary) and stmt.value.op == "+"


def test_compound_index_assign():
    stmt = parse("xs[0] *= 2").statements[0]
    assert isinstance(stmt, ast.IndexAssign)
    assert stmt.value.op == "*"


def test_slice():
    expr = parse("xs[1:3]").statements[0].expr
    assert isinstance(expr, ast.Slice)
    assert expr.start.value == 1 and expr.end.value == 3

    expr = parse("xs[:2]").statements[0].expr
    assert expr.start is None and expr.end.value == 2

    expr = parse("xs[1:]").statements[0].expr
    assert expr.start.value == 1 and expr.end is None

    expr = parse("xs[:]").statements[0].expr
    assert expr.start is None and expr.end is None


def test_index_bukan_slice():
    expr = parse("xs[0]").statements[0].expr
    assert isinstance(expr, ast.Index)


def test_in_operator():
    expr = parse("x in xs").statements[0].expr
    assert isinstance(expr, ast.Binary) and expr.op == "in"

    expr = parse("x not in xs").statements[0].expr
    assert expr.op == "not in"


def test_interp():
    expr = parse('"Halo, ${nama}!"').statements[0].expr
    assert isinstance(expr, ast.Interp)
    assert expr.parts[0] == "Halo, "
    assert isinstance(expr.parts[1], ast.Ident)


def test_interp_hanya_ekspresi():
    try:
        parse('"${let x = 1}"')
        assert False
    except SyntaxErrorTea as e:
        assert "ekspresi" in e.message