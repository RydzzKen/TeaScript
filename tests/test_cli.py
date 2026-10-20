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
