"""Uji paket: metadata pyproject, isi paket, dan instalasi nyata (opsional)."""

import os, sys, zipfile, glob, subprocess, tempfile, venv
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # Python < 3.11
    except ImportError:
        tomllib = None


def read_pyproject():
    if tomllib is None:
        pytest.skip("tomllib/tomli tidak tersedia")
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
        return tomllib.load(f)


def test_metadata_dasar():
    data = read_pyproject()
    proj = data["project"]
    assert proj["name"] == "teascript"
    assert proj["version"].count(".") == 2
    assert proj["scripts"]["tea"] == "teascript.cli:main"
    assert proj["scripts"]["tea-web"] == "teascript.web:main"
    assert "flask" in " ".join(proj["optional-dependencies"]["web"])


def test_versi_cli_sama_dengan_metadata():
    from teascript.cli import main
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(["--version"])
    versi_cli = buf.getvalue().strip().split()[-1]
    assert versi_cli == read_pyproject()["project"]["version"]


def test_init_version_jadi_satu_sumber():
    """teascript.__version__ harus ada dan berformat versi."""
    import teascript
    bagian = teascript.__version__.split(".")
    assert len(bagian) == 3 and all(b.isdigit() for b in bagian)


def test_modul_stdlib_ada_di_disk():
    modul = glob.glob(os.path.join(ROOT, "teascript", "modules", "*.tea"))
    nama = {os.path.basename(m) for m in modul}
    assert {"math.tea", "text.tea", "collections.tea"} <= nama


def test_package_data_ikut_terdaftar():
    data = read_pyproject()
    pattern = data["tool"]["setuptools"]["package-data"]["teascript"]
    assert any("modules" in p for p in pattern), \
        "modul .tea harus ikut terpaket (package-data)"


def test_flask_tidak_wajib():
    """Import teaScript inti tidak boleh butuh Flask."""
    kode = (
        "import sys, importlib\n"
        "mods = [m for m in sys.modules if 'flask' in m]\n"
        "import teascript.evaluator as e\n"
        "e.Evaluator()\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", kode], cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_web_app_tanpa_flask_pesan_jelas(monkeypatch):
    """Web.app() tanpa Flask harus memberi pesan install, bukan crash."""
    import importlib

    real_import_module = importlib.import_module

    def fake_import_module(name, *args, **kwargs):
        if name == "flask":
            raise ImportError("disimulasikan: flask tidak ada")
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    from teascript.lexer import Lexer
    from teascript.parser import Parser
    from teascript.evaluator import Evaluator
    from teascript.errors import RuntimeErrorTea

    with pytest.raises(RuntimeErrorTea) as e:
        Evaluator().run(Parser(Lexer('Web.app("x")').tokenize()).parse())
    assert "Flask" in e.value.message
    assert "pip install" in e.value.message


# --- upaya instalasi nyata: hanya kalau diminta (lambat, butuh venv) ---
@pytest.mark.skipif(os.environ.get("TEASCRIPT_TEST_INSTALL") != "1",
                    reason="set TEASCRIPT_TEST_INSTALL=1 untuk uji instalasi")
def test_install_venv_bersih():
    with tempfile.TemporaryDirectory() as tmp:
        env_dir = os.path.join(tmp, "venv")
        venv.create(env_dir, with_pip=True)
        pip = os.path.join(env_dir, "bin", "pip")
        tea = os.path.join(env_dir, "bin", "tea")

        hasil = subprocess.run([pip, "install", "-q", ROOT],
                               capture_output=True, text=True)
        assert hasil.returncode == 0, hasil.stderr

        # jalan dari folder lain, memakai modul stdlib
        proj = os.path.join(tmp, "proj")
        os.makedirs(proj)
        with open(os.path.join(proj, "a.tea"), "w") as f:
            f.write('import math\nprint(math.floor(2.7))\n')
        out = subprocess.run([tea, "a.tea"], cwd=proj,
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        assert out.stdout.strip() == "2.0"
