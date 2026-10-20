"""CLI TeaScript: `tea file.tea` atau `tea` untuk REPL."""

import sys
import os

# Dukungan `python tea.py` dari root repo tanpa instalasi
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator
from .errors import TeaError, RuntimeErrorTea
from .repl import repl


def run_bytes(data):
    """Jalankan kode TeaScript dari bytes (mis. file yang dipipe)."""
    source = data.decode("utf-8", errors="replace")
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        Evaluator().run(program)
        return 0
    except TeaError as e:
        print(e.format(), file=sys.stderr)
        return 1


def run_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file '{path}' tidak ditemukan", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: tidak bisa membaca '{path}': {e}", file=sys.stderr)
        return 1

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        base_dir = os.path.dirname(os.path.abspath(path))
        Evaluator().run(program, base_dir=base_dir, script_path=path)
        return 0
    except TeaError as e:
        print(e.format(), file=sys.stderr)
        return 1


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)

    if len(args) == 0:
        # stdin dipipe (bukan terminal) → jalankan seperti skrip, jangan REPL
        if not sys.stdin.isatty():
            return run_bytes(sys.stdin.buffer.read())
        repl()
        return 0
    if args[0] in ("-h", "--help"):
        print("Penggunaan: tea <file.tea>")
        print("  tea file.tea   menjalankan file")
        print("  tea -          menjalankan kode dari stdin")
        print("  tea            membuka REPL (tanpa argumen)")
        print("  tea-web        playground web (Flask)")
        return 0
    if args[0] in ("-v", "--version"):
        print("TeaScript 0.3.0")
        return 0
    if args[0] == "-":
        return run_bytes(sys.stdin.buffer.read())
    return run_file(args[0])


if __name__ == "__main__":
    sys.exit(main())
