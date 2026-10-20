import sys, os
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("flask", reason="Flask belum terpasang")

from teascript.web import create_app, run_source


@pytest.fixture()
def client():
    return create_app().test_client()


def post_run(client, source, inputs=None):
    return client.post("/api/run", json={"source": source, "inputs": inputs})


def test_run_ok(client):
    res = post_run(client, "print(1 + 1)")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["output"] == "2\n"


def test_run_error(client):
    data = post_run(client, "let x = ").get_json()
    assert data["ok"] is False
    assert "Error" in data["error"]
    assert data["output"] == ""


def test_run_runtime_error_disertai_output_sebelumnya(client):
    data = post_run(client, 'print("sebelum")\nprint(1 / 0)').get_json()
    assert data["ok"] is False
    assert data["output"] == "sebelum\n"
    assert "nol" in data["error"]


def test_run_dengan_input(client):
    src = 'let nama = input("Siapa? ")\nprint("Halo, ${nama}")'
    data = post_run(client, src, inputs=["Ken"]).get_json()
    assert data["ok"] is True
    assert data["output"] == "Siapa? Ken\nHalo, Ken\n"


def test_run_input_habis(client):
    data = post_run(client, 'print(input("x: "))', inputs=[]).get_json()
    assert data["ok"] is False
    assert "kehabisan" in data["error"]


def test_run_kosong(client):
    res = post_run(client, "   ")
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


def test_run_terlalu_panjang(client):
    res = post_run(client, "// " + "x" * 100_000)
    assert res.status_code == 400
    assert "panjang" in res.get_json()["error"]


def test_run_import_stdlib(client):
    data = post_run(client, "import math\nprint(math.floor(2.7))").get_json()
    assert data["ok"] is True
    assert data["output"] == "2.0\n"


def test_run_pyimport(client):
    data = post_run(client,
                    'let m = pyimport("math")\nprint(m.sqrt(9))').get_json()
    assert data["ok"] is True
    assert data["output"] == "3.0\n"


def test_examples_list(client):
    data = client.get("/api/examples").get_json()
    assert "fizzbuzz.tea" in data["examples"]
    assert all(name.endswith(".tea") for name in data["examples"])


def test_webapp_route_daftar(client):
    """Modul Web: route terdaftar dan bisa dipanggil."""
    src = '''
let flask = pyimport("flask")
let app = flask.Flask("tes")
fn home() { return "HALO" }
fn sapa(nama) { return "Halo, ${nama}!" }
app.route("/")(home)
app.route("/sapa/<nama>")(sapa)
let c = app.test_client()
print(c.get("/").get_data(let _as_text = true))
print(c.get("/sapa/Ken").get_data(let _as_text = true))
'''
    data = post_run(client, src).get_json()
    assert data["ok"] is True, data["error"]
    assert data["output"] == "HALO\nHalo, Ken!\n"


def test_modul_web_bawaan():
    """Modul `Web` menyembunyikan detail Flask."""
    src = '''
let app = Web.app("tes")
fn home() { return "<h1>Halo</h1>" }
app.route("/")(home)
let c = app.test_client()
print(c.get("/").get_data(let _as_text = true))
'''
    hasil = run_source(src)
    assert hasil["ok"] is True, hasil["error"]
    assert hasil["output"] == "<h1>Halo</h1>\n"


def test_modul_web_run_tidak_memblokir_di_test(monkeypatch):
    """`app.run()` harus gagal cepat, bukan menggantung, saat dites."""
    monkeypatch.setenv("TEASCRIPT_NO_BLOCK", "1")
    hasil = run_source('Web.app("tes").run()')
    assert hasil["ok"] is False
    assert "TEASCRIPT_NO_BLOCK" in hasil["error"]


def test_handler_tea_bisa_jadi_handler_flask():
    """Fungsi TeaScript harus benar-benar callable dari Python."""
    src = '''
let app = Web.app("tes")
fn jumlah(a, b) { return a + b }
app.route("/tambah/<int:a>/<int:b>")(jumlah)
let c = app.test_client()
print(c.get("/tambah/20/22").get_data(let _as_text = true))
'''
    hasil = run_source(src)
    assert hasil["ok"] is True, hasil["error"]
    assert hasil["output"] == "42\n"


def test_route_duplikat_terdeteksi():
    """Route yang sama dua kali harus memberi error jelas, bukan diam."""
    src = '''
let app = Web.app("tes")
fn home() { return "a" }
app.route("/")(home)
app.route("/")(home)
'''
    hasil = run_source(src)
    assert hasil["ok"] is False
    assert "route" in hasil["error"].lower()


def test_example_content(client):
    res = client.get("/api/example/fizzbuzz.tea")
    assert res.status_code == 200
    assert "FizzBuzz" in res.get_json()["source"]


def test_example_missing(client):
    assert client.get("/api/example/tidak_ada.tea").status_code == 404
    assert client.get("/api/example/../tea.py").status_code == 404


def test_run_source_langsung():
    hasil = run_source("print(40 + 2)")
    assert hasil == {"ok": True, "output": "42\n", "error": None}
