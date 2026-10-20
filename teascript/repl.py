"""REPL: ketik satu baris, lihat hasilnya."""

from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator, BreakSignal, ContinueSignal
from .errors import TeaError
from . import ast_nodes as ast


def format_value(value):
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(
            f'"{v}"' if isinstance(v, str) else format_value(v)
            for v in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(
            f'"{k}": {format_value(v)}' if isinstance(k, str)
            else f"{k}: {format_value(v)}"
            for k, v in value.items())
        return "{" + items + "}"
    return str(value)


def repl():
    print("TeaScript REPL 0.2 — ketik 'exit' untuk keluar")
    evaluator = Evaluator()
    while True:
        try:
            line = input("tea> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip() in ("exit", "quit"):
            break
        if not line.strip():
            continue
        try:
            tokens = Lexer(line).tokenize()
            program = Parser(tokens).parse()
            result = None
            for stmt in program.statements:
                if isinstance(stmt, ast.ExprStmt):
                    result = evaluator.evaluate(stmt.expr, evaluator.globals)
                else:
                    evaluator.execute(stmt, evaluator.globals)
            if result is not None:
                print(format_value(result))
        except (BreakSignal, ContinueSignal) as s:
            print(f"Error (baris {s.line}): 'break'/'continue' di luar loop")
        except TeaError as e:
            print(e.format())