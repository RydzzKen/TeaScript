import sys, os, io, glob, contextlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from teascript.cli import main, run_file
from test_packaging import read_pyproject


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
    # Contoh yang tidak dijalankan buta:
    #   web.tea    → servernya memblokir (dites terpisah di test_web.py)
    #   gemini.tea → butuh API key & jaringan
    LEWATI = {"web.tea", "gemini.tea"}
    examples = glob.glob(os.path.join(ROOT, "examples", "*.tea"))
    assert examples, "folder examples kosong"
    diuji = 0
    for path in examples:
        if os.path.basename(path) in LEWATI:
            continue
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            code = run_file(path)
        assert code == 0, f"{path} gagal dijalankan"
        assert buf.getvalue(), f"{path} tidak menghasilkan output"
        diuji += 1
    assert diuji >= 4, "terlalu sedikit contoh yang diuji"


def test_contoh_gemini_error_tanpa_key():
    """gemini.tea harus berhenti dengan pesan jelas kalau API key kosong.

    Dijalankan di folder bersih tanpa .env (dan HOME diarahkan ke situ),
    supaya tidak bergantung pada .env di folder atas.
    """
    import tempfile
    path = os.path.join(ROOT, "examples", "gemini.tea")
    with tempfile.TemporaryDirectory() as tmp:
        home_lama = os.environ.get("HOME")
        cwd = os.getcwd()
        os.environ["HOME"] = tmp
        os.environ.pop("GEMINI_API_KEY", None)
        os.chdir(tmp)
        try:
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = run_file(path)
        finally:
            os.chdir(cwd)
            if home_lama is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = home_lama
        assert code == 1
        gabung = out.getvalue() + err.getvalue()
        assert "GEMINI_API_KEY" in gabung


def test_modul_stdlib_env_tidak_bentrok_contoh():
    """Tidak boleh ada file contoh bernama env.tea (menabrak modul stdlib)."""
    assert not os.path.exists(os.path.join(ROOT, "examples", "env.tea")), \
        "examples/env.tea menabrak modul stdlib 'env' — ganti namanya"


def test_tidak_ada_contoh_bentrok_nama_modul_stdlib():
    """File di examples/ tidak boleh bernama sama dengan modul stdlib."""
    modul = {os.path.basename(p)[:-4]
             for p in glob.glob(os.path.join(ROOT, "teascript", "modules", "*.tea"))}
    bentrok = []
    for path in glob.glob(os.path.join(ROOT, "examples", "*.tea")):
        nama = os.path.basename(path)[:-4]
        if nama in modul:
            bentrok.append(nama)
    assert not bentrok, f"contoh bentrok dengan modul stdlib: {bentrok}"


# --- alias perintah & info ---

def test_info_menampilkan_lokasi_paket():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["info"]) == 0
    out = buf.getvalue()
    assert "TeaScript" in out
    assert "paket" in out
    assert "python" in out


def test_help_menyebut_info_dan_sinonim():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert main(["--help"]) == 0
    out = buf.getvalue()
    assert "info" in out
    assert "teascript" in out.lower()


def test_pyproject_punya_alias_teascript():
    data = read_pyproject()
    scripts = data["project"]["scripts"]
    assert "teascript" in scripts, "perintah alternatif 'teascript' hilang"
    assert "teascript-web" in scripts
    assert scripts["teascript"] == scripts["tea"]


def test_import_env_dari_folder_contoh():
    """`import env` di examples/ harus ambil modul stdlib, bukan file contoh."""
    from teascript.lexer import Lexer
    from teascript.parser import Parser
    from teascript.evaluator import Evaluator

    examples = os.path.join(ROOT, "examples")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Evaluator().run(
            Parser(Lexer('import env\nprint(env.load())\n').tokenize()).parse(),
            base_dir=examples)
    # tidak error; hasil true/false tergantung ada tidaknya .env di atas
    assert buf.getvalue().strip() in ("true", "false")


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


# --- output error yang lebih jelas ---

def test_error_menampilkan_cuplikan_baris_sumber():
    """Error runtime harus menampilkan baris sumbernya + penanda ^."""
    import tempfile
    from teascript.cli import run_file
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "salah.tea")
        with open(path, "w") as f:
            f.write("let x = 1\nprint(z)\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = run_file(path)
        assert code == 1
        out = err.getvalue()
        assert "baris 2" in out
        assert "print(z)" in out
        assert "^" in out


def test_error_python_sebut_nama_exception():
    """Error dari fungsi Python harus menyebut jenis exception-nya."""
    import tempfile
    from teascript.cli import run_file
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "py.tea")
        with open(path, "w") as f:
            f.write('let os = pyimport("os")\n'
                    'os.stat("/folder/yang/tidak/ada")\n')
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = run_file(path)
        assert code == 1
        assert "FileNotFoundError" in err.getvalue()


def test_try_catch_di_file():
    """try/catch dipakai lewat CLI: error tertangkap, program lanjut."""
    import tempfile
    from teascript.cli import run_file
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tangkap.tea")
        with open(path, "w") as f:
            f.write("try {\n"
                    "  let x = 1 / 0\n"
                    "} catch e {\n"
                    '  print("tertangkap:", e.message)\n'
                    "}\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = run_file(path)
        assert code == 0
        assert "tertangkap: pembagian dengan nol" in out.getvalue()


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
