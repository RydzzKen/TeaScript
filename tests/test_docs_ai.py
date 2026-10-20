"""docs/AI.md — spesifikasi untuk AI.

Contoh di dalam file itu dijalankan sungguhan, supaya AI tidak pernah
diberi contoh yang salah. Spesifikasi keliru lebih buruk daripada tidak ada.
"""
import os, sys, io, re, contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from teascript.lexer import Lexer
from teascript.parser import Parser
from teascript.evaluator import Evaluator
from teascript.errors import TeaError

SPEC = os.path.join(ROOT, "docs", "AI.md")

# Blok yang memang butuh input pengguna, server, atau jaringan.
BUTUH_LUAR = [
    'let user = input("You : ")',
    "app.run()",
    'requests.get("https://example.com")',
]

UTIL_TEA = 'fn sapa(nama) {\n  return "Halo, " + nama\n}\n'
ENV_TEA = "API_KEY=rahasia\nPORT=5000\nDEBUG=true\nNAMA=Ken\n"


def blok_tea():
    with open(SPEC, encoding="utf-8") as f:
        return re.findall(r"```tea\n(.*?)```", f.read(), re.S)


def blok_bisa_dijalankan():
    return [b for b in blok_tea()
            if not any(x in b for x in BUTUH_LUAR)]


def test_spesifikasi_ai_ada():
    assert os.path.exists(SPEC), "docs/AI.md hilang"
    teks = open(SPEC, encoding="utf-8").read()
    # hal-hal penting yang harus disebut
    assert "fn " in teks
    assert "let " in teks
    assert "pyimport" in teks
    assert "Web.app()" in teks
    assert "env.load()" in teks


def test_ada_cukup_banyak_contoh():
    blok = blok_tea()
    assert len(blok) >= 18, f"terlalu sedikit blok contoh: {len(blok)}"


def test_spesifikasi_tidak_menjanjikan_fitur_yang_belum_ada():
    """Fitur yang belum diimplementasi tidak boleh muncul sebagai contoh.

    Contoh: fungsi anonim `fn(x) { }` belum ada, jadi tidak boleh dipakai
    di blok ```tea mana pun (boleh disebut di tabel kesalahan).
    """
    for i, blok in enumerate(blok_tea(), 1):
        assert "fn(" not in blok, (
            f"blok {i} memakai fungsi anonim `fn(...)` yang belum ada")
        assert "=>" not in blok, f"blok {i} memakai arrow function yang belum ada"


def test_semua_contoh_ai_berjalan(tmp_path):
    """Setiap blok ```tea bisa dijalankan tanpa error."""
    gagal = []
    for i, src in enumerate(blok_bisa_dijalankan(), 1):
        kerja = tmp_path / f"blok{i}"
        kerja.mkdir()
        (kerja / "util.tea").write_text(UTIL_TEA)
        (kerja / ".env").write_text(ENV_TEA)

        ev = Evaluator()
        ev.input_fn = lambda prompt="": "halo"
        try:
            prog = Parser(Lexer(src).tokenize()).parse()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ev.run(prog, base_dir=str(kerja))
        except TeaError as e:
            baris1 = src.strip().splitlines()[0]
            gagal.append(f"blok {i}: {e.message or e} | {baris1}")
        except Exception as e:  # noqa: BLE001
            baris1 = src.strip().splitlines()[0]
            gagal.append(f"blok {i}: {type(e).__name__}: {e} | {baris1}")

    assert not gagal, "contoh di docs/AI.md gagal:\n" + "\n".join(gagal)


def test_minimal_separuh_contoh_diuji():
    """Jangan sampai filternya terlalu longgar sehingga hampir tak diuji."""
    total = len(blok_tea())
    diuji = len(blok_bisa_dijalankan())
    dilewati = total - diuji
    # hanya boleh lewat karena butuh jaringan/server, maksimal 4 blok
    assert dilewati <= 4, (
        f"terlalu banyak blok dilewati: {dilewati} dari {total}")
    assert diuji >= 15, f"terlalu sedikit blok diuji: {diuji}"
