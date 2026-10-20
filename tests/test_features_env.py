"""Uji fitur baru: default parameter, error/getenv/setenv, modul env."""

import sys, os, io, contextlib, tempfile, textwrap
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript.evaluator import Evaluator
from teascript.errors import RuntimeErrorTea, SyntaxErrorTea


def run(src, base_dir=None):
    ev = Evaluator()
    ev.run(Parser(Lexer(src).tokenize()).parse(), base_dir=base_dir)
    return ev


def capture(src, base_dir=None):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(src, base_dir=base_dir)
    return buf.getvalue()


def expect_error(src, cls=RuntimeErrorTea):
    try:
        run(src)
    except cls as e:
        return e
    raise AssertionError(f"seharusnya error: {src}")


# --- default parameter ---
def test_default_dipakai_kalau_kurang():
    out = capture(textwrap.dedent("""
        fn sapa(nama, sapaan = "Halo") {
          return sapaan + ", " + nama
        }
        print(sapa("Ken"))
        print(sapa("Ken", "Yo"))
    """))
    assert out == "Halo, Ken\nYo, Ken\n"


def test_default_beberapa_dan_berurutan():
    out = capture(textwrap.dedent("""
        fn tambah(a, b = 10, c = 100) { return a + b + c }
        print(tambah(1))
        print(tambah(1, 2))
        print(tambah(1, 2, 3))
    """))
    assert out == "111\n103\n6\n"


def test_default_dihitung_saat_dipanggil():
    """Default dievaluasi tiap panggilan, bukan sekali saat definisi."""
    out = capture(textwrap.dedent("""
        let n = 1
        fn f(x = n) { return x }
        print(f())
        n = 99
        print(f())
    """))
    assert out == "1\n99\n"


def test_kurang_argumen_tanpa_default_error():
    e = expect_error(textwrap.dedent("""
        fn f(a, b) { return a }
        f(1)
    """))
    assert "minimal 2 argumen" in e.message


def test_kelebihan_argumen_error():
    e = expect_error(textwrap.dedent("""
        fn f(a, b = 1) { return a }
        f(1, 2, 3)
    """))
    assert "maksimal 2 argumen" in e.message


def test_default_lalu_wajib_ditolak():
    e = expect_error('fn f(a = 1, b) { return a }', cls=SyntaxErrorTea)
    assert "default" in e.message


# --- error() ---
def test_error_builtin():
    e = expect_error('error("ada masalah")')
    assert e.message == "ada masalah"


def test_error_gabung_argumen():
    e = expect_error('error("kode", 404)')
    assert e.message == "kode 404"


# --- getenv / setenv ---
def test_setenv_getenv():
    out = capture(textwrap.dedent("""
        setenv("TEASCRIPT_UJI_X", "halo")
        print(getenv("TEASCRIPT_UJI_X"))
        print(getenv("TEASCRIPT_UJI_X"))
    """))
    assert out == "halo\nhalo\n"
    os.environ.pop("TEASCRIPT_UJI_X", None)


def test_getenv_default():
    out = capture('print(getenv("TEASCRIPT_TIDAK_MUNGKIN_ADA", "cadangan"))')
    assert out == "cadangan\n"


def test_getenv_tanpa_default_nil():
    out = capture('print(getenv("TEASCRIPT_TIDAK_MUNGKIN_ADA"))')
    assert out == "nil\n"


def test_getenv_butuh_string():
    e = expect_error("getenv(123)")
    assert "string" in e.message


# --- modul env ---
ENV_ISI = """\
# komentar
NAMA=Ken
KOTA="Surabaya"
PORT=8080
DEBUG=true
export MODE=dev
URL=https://${KOTA}.example.com/$PORT
HARGA='100'   # komentar di tengah
"""


def with_env_project(func):
    """Buat folder sementara berisi .env, jalankan func di dalamnya."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".env"), "w", encoding="utf-8") as f:
            f.write(ENV_ISI)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            func(tmp)
        finally:
            os.chdir(cwd)


def test_env_load_dan_get():
    def cek(tmp):
        out = capture(textwrap.dedent("""
            import env
            print(env.load())
            print(env.get("NAMA"))
            print(env.get("KOTA"))
        """), base_dir=tmp)
        assert out == "true\nKen\nSurabaya\n"
    with_env_project(cek)


def test_env_parse_kutip_komentar_export_interpolasi():
    def cek(tmp):
        out = capture(textwrap.dedent("""
            import env
            env.load()
            print(env.get("HARGA"))
            print(env.get("MODE"))
            print(env.get("URL"))
        """), base_dir=tmp)
        assert out == "100\ndev\nhttps://Surabaya.example.com/8080\n"
    with_env_project(cek)


def test_env_num_dan_bool():
    def cek(tmp):
        out = capture(textwrap.dedent("""
            import env
            env.load()
            print(env.get_num("PORT"))
            print(env.get_bool("DEBUG"))
            print(env.get_bool("TIDAK_ADA", true))
        """), base_dir=tmp)
        assert out == "8080\ntrue\ntrue\n"
    with_env_project(cek)


def test_env_cari_ke_folder_induk():
    """Dijalankan dari subfolder, .env di induk tetap ketemu."""
    def cek(tmp):
        dalam = os.path.join(tmp, "a", "b")
        os.makedirs(dalam)
        cwd = os.getcwd()
        os.chdir(dalam)
        try:
            out = capture(textwrap.dedent("""
                import env
                env.load()
                print(env.get("NAMA"))
            """), base_dir=dalam)
        finally:
            os.chdir(cwd)
        assert out == "Ken\n"
    with_env_project(cek)


def test_env_load_tanpa_file_false():
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            out = capture("import env\nprint(env.load())", base_dir=tmp)
        finally:
            os.chdir(cwd)
        # tidak ada .env di mana pun sampai root → false
        assert out == "false\n"


def test_env_wajib_error_kalau_kosong():
    def cek(tmp):
        e = None
        try:
            run('import env\nenv.load()\nenv.wajib("NGGAK_ADA")', base_dir=tmp)
        except RuntimeErrorTea as err:
            e = err
        assert e is not None and "NGGAK_ADA" in e.message
    with_env_project(cek)


def test_env_parse_langsung():
    out = capture(textwrap.dedent("""
        import env
        let peta = env.parse("A=1\\nB=dua\\n# lewat\\nKOSONG=\\n")
        print(keys(peta))
        print(peta["A"])
        print(peta["B"])
    """))
    assert '"A"' in out and '"B"' in out and '"KOSONG"' in out
    assert "1\ndua\n" in out


def test_env_semua():
    def cek(tmp):
        out = capture(textwrap.dedent("""
            import env
            env.load()
            print(env.semua()["NAMA"])
        """), base_dir=tmp)
        assert out == "Ken\n"
    with_env_project(cek)


def test_env_script_bernama_env_tidak_impor_diri_sendiri():
    """examples/env.tea → `import env` harus ambil modul stdlib, bukan dirinya."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".env"), "w", encoding="utf-8") as f:
            f.write("NAMA=Ken\n")
        script = os.path.join(tmp, "env.tea")
        # file bernama env.tea yang mengimpor "env"
        with open(script, "w", encoding="utf-8") as f:
            f.write("import env\nenv.load()\nprint(env.get(\"NAMA\"))\n")

        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                Evaluator().run(
                    Parser(Lexer(open(script).read()).tokenize()).parse(),
                    base_dir=tmp, script_path=script)
        finally:
            os.chdir(cwd)
        assert buf.getvalue() == "Ken\n"


def test_impor_diri_sendiri_tanpa_alternatif_error():
    """Kalau tidak ada alternatif (bukan stdlib), impor diri → error melingkar."""
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "unik.tea")
        with open(script, "w", encoding="utf-8") as f:
            f.write("import unik\n")
        e = None
        try:
            Evaluator().run(
                Parser(Lexer(open(script).read()).tokenize()).parse(),
                base_dir=tmp, script_path=script)
        except RuntimeErrorTea as err:
            e = err
        assert e is not None and "melingkar" in e.message
