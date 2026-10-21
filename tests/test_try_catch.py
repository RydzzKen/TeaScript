"""try / catch — menangkap error, lalu melanjutkan program.

try { ... } catch e { ... }
try { ... } catch { ... }   (tanpa variabel)
"""
import sys, os, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript.evaluator import Evaluator
from teascript.errors import NameErrorTea, RuntimeErrorTea, TeaError


def run(src):
    tokens = Lexer(src).tokenize()
    program = Parser(tokens).parse()
    Evaluator().run(program)


def capture(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(src)
    return buf.getvalue()


def capture_error(src):
    """Jalankan, kembalikan error yanguncaught."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            run(src)
    except TeaError as e:
        return e
    raise AssertionError("errornya_expected_uncaught")


# --- parse ---

def test_parser_baca_try_catch():
    program = Parser(Lexer("try { print(1) } catch e { print(2) }").tokenize()).parse()
    assert len(program.statements) == 1
    node = program.statements[0]
    assert node.has_catch is True
    assert node.catch_var == "e"
    assert len(node.body) == 1
    assert len(node.catch_body) == 1


def test_parser_catch_tanpa_variabel():
    program = Parser(Lexer("try { print(1) } catch { print(2) }").tokenize()).parse()
    node = program.statements[0]
    assert node.has_catch is True
    assert node.catch_var is None


def test_parser_try_tanpa_catch():
    program = Parser(Lexer("try { print(1) }").tokenize()).parse()
    node = program.statements[0]
    assert node.has_catch is False


# --- menangkap error ---

def test_tangkap_error_runtime():
    src = """
    try {
      let x = 1 / 0
    } catch e {
      print(e.message)
    }
    """
    assert capture(src) == "pembagian dengan nol\n"


def test_tangkap_nama_variabel():
    src = """
    try {
      print(tidak_ada)
    } catch e {
      print(e.message)
    }
    """
    assert capture(src) == "variabel 'tidak_ada' belum dideklarasikan\n"


def test_tangkap_error_builtin():
    src = """
    try {
      error("boom")
    } catch e {
      print(e.message)
    }
    """
    assert capture(src) == "boom\n"


def test_tangkap_error_python_pyimport():
    src = """
    let os = pyimport("os")
    try {
      os.stat("/folder/yang/tidak/ada/sekali")
    } catch e {
      print(e.kind)
      print(e.message)
    }
    """
    out = capture(src)
    assert out.startswith("python\n")
    assert "FileNotFoundError" in out


def test_blok_setelah_error_tidak_dijalankan():
    src = """
    try {
      let x = 1 / 0
      print("tidak boleh tercetak")
    } catch e {
      print("tertangkap")
    }
    print("lanjut")
    """
    assert capture(src) == "tertangkap\nlanjut\n"


def test_catch_tanpa_variabel_menelan_error():
    src = """
    try {
      let x = 1 / 0
    } catch {
      print("ditelan")
    }
    print("lanjut")
    """
    assert capture(src) == "ditelan\nlanjut\n"


def test_tanpa_catch_error_naik_begitu_saja():
    err = capture_error("try { let x = 1 / 0 }")
    assert "pembagian dengan nol" in err.message


def test_error_di_setelah_try_tidak_tertangkap():
    src = """
    try {
      print("aman")
    } catch e {
      print("tidak jalan")
    }
    let x = 1 / 0
    """
    err = capture_error(src)
    assert "pembagian dengan nol" in err.message


# --- isi variabel catch ---

def test_variabel_catch_punya_field():
    src = """
    try {
      let x = 1 / 0
    } catch e {
      print(e.kind)
      print(e.line)
      print(e.column)
      print(type(e))
    }
    """
    out = capture(src)
    assert out.splitlines()[0] == "runtime"
    assert out.splitlines()[1] == "3"
    assert out.splitlines()[2].isdigit()
    assert out.splitlines()[3] == "error"


def test_str_error_punya_posisi():
    src = """
    try {
      let x = 1 / 0
    } catch e {
      print(str(e))
    }
    """
    out = capture(src)
    assert out.startswith("Error (baris 3")
    assert "pembagian dengan nol" in out


def test_variabel_catch_ada_di_lingkup_fungsi():
    src = """
    fn cek() {
      try {
        let x = 1 / 0
      } catch e {
        return e.message
      }
      return "tidak tertangkap"
    }
    print(cek())
    """
    assert capture(src) == "pembagian dengan nol\n"


# --- kendali alur tetap jalan ---

def test_return_di_dalam_try_bukan_error():
    src = """
    fn f() {
      try {
        return "dari try"
      } catch e {
        return "dari catch"
      }
    }
    print(f())
    """
    assert capture(src) == "dari try\n"


def test_break_dan_continue_di_dalam_try():
    src = """
    for i in range(5) {
      try {
        if i == 2 { continue }
        if i == 4 { break }
        print(i)
      } catch e {
        print("catch")
      }
    }
    """
    assert capture(src) == "0\n1\n3\n"


# --- try bersarang ---

def test_try_bersarang():
    src = """
    try {
      try {
        let x = 1 / 0
      } catch e {
        print("dalam")
        throw_like()
      }
    } catch e {
      print("luar")
    }
    """
    # throw_like tidak ada -> error NameErrorTea ditangkap catch luar
    assert capture(src) == "dalam\nluar\n"


def test_catch_luar_menangkap_error_dari_catch_dalam():
    src = """
    try {
      try {
        let x = 1 / 0
      } catch e {
        let y = 1 / 0
      }
    } catch e {
      print(e.message)
    }
    """
    assert capture(src) == "pembagian dengan nol\n"


# --- dipakai di loop & repeatedly ---

def test_catch_dalam_loop():
    src = """
    for i in range(3) {
      try {
        let x = 10 / i
        print(x)
      } catch e {
        print("takut")
      }
    }
    """
    assert capture(src) == "takut\n10.0\n5.0\n"
