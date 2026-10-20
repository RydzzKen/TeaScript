import sys, os, io, contextlib, textwrap
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript.evaluator import Evaluator
from teascript.errors import TeaError, RuntimeErrorTea, SyntaxErrorTea
from teascript import ast_nodes as ast


def parse(src):
    return Parser(Lexer(src).tokenize()).parse()


def run(src, base_dir=None, evaluator=None):
    ev = evaluator or Evaluator()
    ev.run(parse(src), base_dir=base_dir)
    return ev


def capture(src, base_dir=None):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(src, base_dir=base_dir)
    return buf.getvalue()


def write(dirpath, name, source):
    path = os.path.join(dirpath, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(source))
    return path


# --- parser ---
def test_parse_import():
    stmt = parse("import math").statements[0]
    assert isinstance(stmt, ast.Import)
    assert stmt.name == "math" and stmt.path is None


def test_parse_import_path():
    stmt = parse('import "lib/util.tea"').statements[0]
    assert isinstance(stmt, ast.Import)
    assert stmt.name == "util" and stmt.path == "lib/util.tea"


def test_parse_from_import():
    stmt = parse("from math import sqrt, pow").statements[0]
    assert isinstance(stmt, ast.FromImport)
    assert stmt.module == "math"
    assert stmt.names == ["sqrt", "pow"]


def test_parse_dot_access():
    expr = parse("math.sqrt(2)").statements[0].expr
    assert isinstance(expr, ast.Call)
    assert isinstance(expr.callee, ast.Index)
    assert expr.callee.index.value == "sqrt"


def test_parse_dot_chain():
    expr = parse("a.b.c").statements[0].expr
    assert isinstance(expr, ast.Index)
    assert isinstance(expr.target, ast.Index)
    assert expr.index.value == "c"


# --- modul lokal ---
def test_import_modul_lokal(tmp_path):
    write(str(tmp_path), "util.tea", """
        fn sapa(n) { return "Halo, ${n}" }
        let bahasa = "TeaScript"
    """)
    out = capture('import util\nprint(util.sapa("Ken"))\nprint(util.bahasa)',
                  base_dir=str(tmp_path))
    assert out == "Halo, Ken\nTeaScript\n"


def test_from_import_lokal(tmp_path):
    write(str(tmp_path), "util.tea", "fn ganda(x) { return x * 2 }\n")
    out = capture("from util import ganda\nprint(ganda(21))",
                  base_dir=str(tmp_path))
    assert out == "42\n"


def test_import_dalam_folder_lib(tmp_path):
    write(str(tmp_path), "lib/konversi.tea",
          "fn c2f(c) { return c * 9 / 5 + 32 }\n")
    out = capture('import "lib/konversi.tea"\nprint(konversi.c2f(100))',
                  base_dir=str(tmp_path))
    assert out == "212.0\n"


def test_modul_dipanggil_hanya_sekali(tmp_path):
    # modul yang mencetak saat dieksekusi tidak boleh dieksekusi ulang
    write(str(tmp_path), "sekali.tea", 'let hitung = 0\nprint("dimuat")\n')
    ev = Evaluator()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run("import sekali\nimport sekali", base_dir=str(tmp_path), evaluator=ev)
        run("import sekali", base_dir=str(tmp_path), evaluator=ev)
    assert buf.getvalue() == "dimuat\n"


def test_privat_tidak_diekspor(tmp_path):
    write(str(tmp_path), "util.tea", "let _rahasia = 99\nlet umum = 1\n")
    out = capture('from util import umum\nprint(umum)', base_dir=str(tmp_path))
    assert out == "1\n"
    for src in ("import util\nprint(util._rahasia)",
                "from util import _rahasia"):
        try:
            run(src, base_dir=str(tmp_path))
            assert False, f"privat bocor: {src}"
        except TeaError as e:
            assert "_rahasia" in e.message


def test_import_melingkar(tmp_path):
    write(str(tmp_path), "a.tea", "import b\n")
    write(str(tmp_path), "b.tea", "import a\n")
    try:
        run("import a", base_dir=str(tmp_path))
        assert False
    except RuntimeErrorTea as e:
        assert "melingkar" in e.message
        assert "a.tea" in e.message and "b.tea" in e.message


def test_error_sintaks_modul_sebut_nama_file(tmp_path):
    write(str(tmp_path), "rusak.tea", "let x = \n")
    try:
        run("import rusak", base_dir=str(tmp_path))
        assert False
    except SyntaxErrorTea as e:
        assert "rusak.tea" in e.message


def test_modul_tidak_ada():
    try:
        run("import tidak_ada_modul_xyz")
        assert False
    except RuntimeErrorTea as e:
        assert "tidak ditemukan" in e.message


def test_ekspor_tidak_ada():
    try:
        run("from math import fungsi_tidak_ada")
        assert False
    except RuntimeErrorTea as e:
        assert "tidak mengekspor" in e.message


def test_env_teascript_path(tmp_path, monkeypatch):
    mod_dir = tmp_path / "modul_luar"
    mod_dir.mkdir()
    (mod_dir / "khusus.tea").write_text("fn halo() { return \"ok\" }\n")
    monkeypatch.setenv("TEASCRIPT_PATH", str(mod_dir))
    out = capture("import khusus\nprint(khusus.halo())")
    assert out == "ok\n"


# --- stdlib ---
def test_stdlib_math():
    out = capture("import math\n"
                  "print(math.sqrt(2))\n"
                  "print(math.pow(2, 10))\n"
                  "print(math.round(3.6), math.floor(-3.2), math.ceil(-3.2))\n"
                  "print(math.clamp(15, 0, 10), math.lerp(0, 10, 0.5))")
    lines = out.splitlines()
    assert abs(float(lines[0]) - 1.4142135623730951) < 1e-12
    assert lines[1] == "1024"
    assert lines[2] == "4.0 -5.0 -4.0"
    assert lines[3] == "10 5.0"


def test_stdlib_text():
    out = capture("import text\n"
                  "print(text.capitalize(\"halo\"))\n"
                  "print(text.title(\"halo DUNIA\") )\n"
                  "print(text.repeat(\"ab\", 3))\n"
                  "print(text.replace_all(\"a-b-c\", \"-\", \"+\"))\n"
                  "print(text.is_blank(\"   \"), text.starts_with(\"abc\", \"ab\"),"
                  " text.ends_with(\"abc\", \"bc\"))")
    lines = out.splitlines()
    assert lines[0] == "Halo"
    assert lines[1] == "Halo Dunia"
    assert lines[2] == "ababab"
    assert lines[3] == "a+b+c"
    assert lines[4] == "true true true"


def test_stdlib_collections():
    out = capture("from collections import sum, product, reverse, unique, count,"
                  " flatten\n"
                  "print(sum([1, 2, 3]), product([2, 3, 4]))\n"
                  "print(reverse([1, 2, 3]))\n"
                  "print(unique([1, 1, 2, 3, 3]))\n"
                  "print(count([1, 2, 1], 1))\n"
                  "print(flatten([[1, 2], [3]]))")
    lines = out.splitlines()
    assert lines[0] == "6 24"
    assert lines[1] == "[3, 2, 1]"
    assert lines[2] == "[1, 2, 3]"
    assert lines[3] == "2"
    assert lines[4] == "[1, 2, 3]"


# --- pyimport ---
def test_pyimport_math():
    out = capture('let m = pyimport("math")\nprint(m.sqrt(144))')
    assert out == "12.0\n"


def test_pyimport_json():
    out = capture('let j = pyimport("json")\nprint(j.dumps({a: 1, b: [true, nil]}))')
    assert out == '{"a": 1, "b": [true, null]}\n'


def test_pyimport_type():
    out = capture('print(type(pyimport("math")))')
    assert out == "module\n"


def test_pyimport_tidak_ada():
    try:
        run('pyimport("modul_py_tidak_ada_xyz")')
        assert False
    except RuntimeErrorTea as e:
        assert "pyimport()" in e.message
        assert "tidak ditemukan" in e.message


def test_pyimport_atribut_tidak_ada():
    try:
        run('let m = pyimport("math")\nprint(m.fungsi_tidak_ada)')
        assert False
    except RuntimeErrorTea as e:
        assert "atribut" in e.message
        assert e.line == 2


def test_pyimport_argumen_bukan_string():
    try:
        run("pyimport(123)")
        assert False
    except RuntimeErrorTea as e:
        assert "string" in e.message


# --- dot access biasa ---
def test_dot_pada_dict():
    assert capture('let d = {nama: "budi"}\nprint(d.nama)') == "budi\n"


def test_dot_bukan_atribut_function():
    # atribut internal Function tidak boleh bocor
    try:
        run("fn f() { return 1 }\nprint(f.params)")
        assert False
    except RuntimeErrorTea as e:
        assert "tidak mendukung indeks" in e.message or "atribut" in e.message
