import sys, os, io, glob, contextlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from teascript.cli import main, run_file


def test_help():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["--help"]) == 0
    assert "Penggunaan" in buf.getvalue()


def test_version():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["--version"]) == 0
    assert "TeaScript" in buf.getvalue()


def test_file_tidak_ditemukan():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        assert main(["tidak_ada.tea"]) == 1
    assert "tidak ditemukan" in buf.getvalue()


def test_semua_contoh_berjalan():
    # Contoh server web tidak dijalankan buta: server-nya memblokir,
    # dan file itu dites terpisah di tests/test_web.py
    examples = glob.glob(os.path.join(ROOT, "examples", "*.tea"))
    assert examples, "folder examples kosong"
    diuji = 0
    for path in examples:
        if os.path.basename(path) == "web.tea":
            continue
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            code = run_file(path)
        assert code == 0, f"{path} gagal dijalankan"
        assert buf.getvalue(), f"{path} tidak menghasilkan output"
        diuji += 1
    assert diuji >= 4, "terlalu sedikit contoh yang diuji"


# --- tea check ---

def test_check_file_bersih(tmp_path=None):
    import tempfile
    from teascript.cli import check_file
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "bersih.tea")
        with open(path, "w") as f:
            f.write('let x = 1\nprint(x)\n')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert check_file(path) == 0
        assert "OK" in buf.getvalue()


def test_check_file_karakter_aneh():
    import tempfile
    from teascript.cli import check_file
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "kotor.tea")
        with open(path, "wb") as f:
            f.write("let x = 1\u00a0\n".encode("utf-8"))
            f.write(b"let y = 2\r\n")
            f.write('let \u201cnama\u201d = 3\n'.encode("utf-8"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = check_file(path)
        out = buf.getvalue()
        assert code == 1
        assert "U+00A0" in out
        assert "U+201C" in out
        assert "CRLF" in out


def test_check_lewat_main():
    import tempfile
    from teascript.cli import main
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "x.tea")
        with open(path, "wb") as f:
            f.write("let x = 1\u00a0\n".encode("utf-8"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert main(["check", path]) == 1
        assert "U+00A0" in buf.getvalue()


def test_check_butuh_argumen():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        assert main(["check"]) == 1
    assert "Penggunaan" in buf.getvalue()


def test_check_file_tidak_ada():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        assert main(["check", "tidak_ada_sama_sekali.tea"]) == 1
    assert "tidak ditemukan" in buf.getvalue()


def test_lexer_tolak_identifier_non_ascii():
    from teascript.lexer import Lexer
    from teascript.errors import SyntaxErrorTea
    try:
        Lexer("let \uff4e = 1").tokenize()
    except SyntaxErrorTea as e:
        assert "U+FF4E" in e.message
    else:
        raise AssertionError("identifier full-width seharusnya ditolak")


def test_lexer_pesan_karakter_pintar():
    from teascript.lexer import Lexer
    from teascript.errors import SyntaxErrorTea
    try:
        Lexer("let x = 1\u201d\n").tokenize()
    except SyntaxErrorTea as e:
        assert "kutip" in e.message.lower()
    else:
        raise AssertionError("kutip pintar seharusnya ditolak")
