"""Webapp TeaScript — server Flask: API eksekusi + playground.

Jalankan:
    python3 webapp.py            (dari root repo)
    tea-web                      (setelah pip install .)
"""

import io
import os
import sys
import contextlib

from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator
from .errors import TeaError, RuntimeErrorTea
from .cli import run_file

try:
    from flask import Flask, request, jsonify
except ImportError:  # pesan ramah jika Flask belum terpasang
    Flask = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(ROOT, "examples")
MAX_SOURCE = 100_000
MAX_INPUTS = 100


def run_source(source, inputs=None):
    """Jalankan kode TeaScript, kembalikan dict {ok, output, error}."""
    buf = io.StringIO()
    queue = [str(v) for v in (inputs or [])][:MAX_INPUTS]

    def input_fn(prompt=""):
        # input() di web dijawab dari daftar input pengguna, bukan terminal
        if not queue:
            raise RuntimeErrorTea("input() kehabisan input dari pengguna")
        value = queue.pop(0)
        buf.write(prompt + value + "\n")
        return value

    ev = Evaluator(input_fn=input_fn)
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        with contextlib.redirect_stdout(buf):
            ev.run(program, base_dir=EXAMPLES_DIR)
        return {"ok": True, "output": buf.getvalue(), "error": None}
    except TeaError as e:
        return {"ok": False, "output": buf.getvalue(), "error": e.format()}


def create_app():
    if Flask is None:
        raise SystemExit(
            "Flask belum terpasang. Install dengan:\n"
            "  python3 -m pip install 'teascript[web]'\n"
            "atau: python3 -m pip install flask")

    app = Flask(__name__)

    @app.get("/")
    def index():
        # Playground UI belum dibuat (fokus proyek sekarang: terminal).
        # Endpoint tetap terdaftar agar tidak ada rute mati.
        return jsonify({
            "name": "TeaScript web",
            "status": "API aktif, playground UI belum tersedia",
            "endpoints": [
                "POST /api/run",
                "GET /api/examples",
                "GET /api/example/<nama>",
            ],
            "cara": 'POST /api/run dengan {"source": "...", "inputs": []}',
        })

    @app.post("/api/run")
    def api_run():
        data = request.get_json(silent=True) or {}
        source = data.get("source")
        if not isinstance(source, str) or not source.strip():
            return jsonify({"ok": False, "output": "",
                            "error": "kode kosong"}), 400
        if len(source) > MAX_SOURCE:
            return jsonify({"ok": False, "output": "",
                            "error": f"kode terlalu panjang "
                                     f"(maks {MAX_SOURCE} karakter)"}), 400
        inputs = data.get("inputs")
        if not isinstance(inputs, list):
            inputs = []
        return jsonify(run_source(source, inputs))

    @app.get("/api/examples")
    def api_examples():
        names = sorted(n for n in os.listdir(EXAMPLES_DIR)
                       if n.endswith(".tea"))
        return jsonify({"examples": names})

    @app.get("/api/example/<name>")
    def api_example(name):
        # Hanya nama file .tea di dalam examples/, tanpa jalur
        safe = os.path.basename(name.strip())
        if not safe.endswith(".tea") or safe != name.strip():
            return jsonify({"error": "contoh tidak ditemukan"}), 404
        path = os.path.join(EXAMPLES_DIR, safe)
        if not os.path.isfile(path):
            return jsonify({"error": "contoh tidak ditemukan"}), 404
        with open(path, "r", encoding="utf-8") as f:
            return jsonify({"name": safe, "source": f.read()})

    return app


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="tea-web",
        description="Jalankan server web TeaScript")
    parser.add_argument("file", nargs="?", default=None,
                        help="file .tea berisi server (mis. examples/web.tea)")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    if args.file is None:
        # Tanpa file: server API/playground standar
        app = create_app()
        host = args.host or "127.0.0.1"
        port = args.port or 5000
        print(f"TeaScript playground → http://{host}:{port}")
        app.run(host=host, port=port, debug=args.debug)
        return 0

    # Dengan file: jalankan file .tea sebagai server web
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: file '{path}' tidak ditemukan", file=sys.stderr)
        return 1

    argv_tea = []
    if args.host:
        # diteruskan lewat env agar file .tea bisa membacanya bila perlu
        os.environ["TEASCRIPT_HOST"] = args.host
    if args.port:
        os.environ["TEASCRIPT_PORT"] = str(args.port)

    print(f"Menjalankan server dari {path} → http://"
          f"{os.environ.get('TEASCRIPT_HOST', '127.0.0.1')}:"
          f"{os.environ.get('TEASCRIPT_PORT', '5000')}")
    return run_file(path)


if __name__ == "__main__":
    raise SystemExit(main())
