"""Uji examples/web.tea sebagai server sungguhan (HTTP lewat port lokal)."""

import sys, os, socket, subprocess, time, json
import urllib.request
import urllib.error
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from teascript.web import run_source

WEB_FILE = os.path.join(ROOT, "examples", "web.tea")


def test_web_file_ada():
    assert os.path.isfile(WEB_FILE), "examples/web.tea hilang"


def test_route_web_file_terdaftar():
    """Jalankan isi web.tea tanpa app.run(), cek tiap route lewat test client."""
    source = open(WEB_FILE, encoding="utf-8").read()
    source = source.replace("app.run()", "// app.run() dites terpisah")

    src = source + '''
let c = app.test_client()
print(c.get("/").status_code)
print(c.get("/sapa/Ken").get_data(let _as_text = true))
print(c.get("/info").get_data(let _as_text = true))
print(c.get("/usia/21").get_data(let _as_text = true))
print(c.get("/tidak-ada").status_code)
'''
    hasil = run_source(src)
    assert hasil["ok"] is True, hasil["error"]
    lines = [b for b in hasil["output"].splitlines() if b.strip()]
    assert lines[0] == "200"
    assert lines[1] == "Halo, Ken!"
    assert json.loads(lines[2])["nama"] == "TeaScript"
    assert lines[3] == "42"
    assert lines[4] == "404"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_server_http_sungguhan():
    port = _free_port()
    env = dict(os.environ)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "webapp.py"),
         WEB_FILE, "--port", str(port)],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        # tunggu server siap
        for _ in range(60):
            try:
                urllib.request.urlopen(base + "/", timeout=1).read()
                break
            except Exception:
                if proc.poll() is not None:
                    out = proc.stdout.read().decode()
                    pytest.fail(f"server mati: {out}")
                time.sleep(0.25)
        else:
            pytest.fail("server tidak siap dalam waktu tunggu")

        def get(path):
            with urllib.request.urlopen(base + path, timeout=3) as r:
                return r.status, r.read().decode()

        status, body = get("/")
        assert status == 200 and "TeaScript web" in body

        status, body = get("/sapa/Ken")
        assert status == 200 and body == "Halo, Ken!"

        status, body = get("/usia/21")
        assert status == 200 and body == "42"

        status, body = get("/info")
        assert status == 200 and json.loads(body)["versi"] == "0.3.0"

        with pytest.raises(urllib.error.HTTPError) as e:
            get("/tidak-ada")
        assert e.value.code == 404
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
