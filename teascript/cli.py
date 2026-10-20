"""CLI TeaScript: `tea file.tea` atau `tea` untuk REPL."""

import sys
import os

# Dukungan `python tea.py` dari root repo tanpa instalasi
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator
from .errors import TeaError, RuntimeErrorTea
from .repl import repl


def run_bytes(data):
    """Jalankan kode TeaScript dari bytes (mis. file yang dipipe)."""
    source = data.decode("utf-8", errors="replace")
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        Evaluator().run(program)
        return 0
    except TeaError as e:
        print(e.format(), file=sys.stderr)
        return 1


def run_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file '{path}' tidak ditemukan", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: tidak bisa membaca '{path}': {e}", file=sys.stderr)
        return 1

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        base_dir = os.path.dirname(os.path.abspath(path))
        Evaluator().run(program, base_dir=base_dir, script_path=path)
        return 0
    except TeaError as e:
        print(e.format(), file=sys.stderr)
        return 1


def check_file(path):
    """Periksa file .tea: laporkan karakter aneh, masalah baris/kolom.

    Berguna saat copy-paste dari web/aplikasi yang menyelipkan karakter
    "mirip" (spasi tak-putus, kutip pintar, full-width).
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: file '{path}' tidak ditemukan", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: tidak bisa membaca '{path}': {e}", file=sys.stderr)
        return 1

    masalah = []

    if data.startswith(b"\xef\xbb\xbf"):
        masalah.append(("-- ", 1, "BOM (byte-order mark) di awal file"))

    baris_ke = 1
    kolom_ke = 1
    i = 0
    while i < len(data):
        b = data[i]
        if b == 0x0A:
            baris_ke += 1
            kolom_ke = 1
            i += 1
            continue
        if b == 0x0D:
            if i + 1 < len(data) and data[i + 1] == 0x0A:
                masalah.append((f"{baris_ke}:{kolom_ke}", baris_ke,
                                "akhir baris CRLF (Windows)"))
                i += 2
                baris_ke += 1
                kolom_ke = 1
                continue
            masalah.append((f"{baris_ke}:{kolom_ke}", baris_ke,
                            "karakter CR sendirian (Mac lama)"))
            i += 1
            baris_ke += 1
            kolom_ke = 1
            continue
        if b == 0x09:
            kolom_ke += 1
            i += 1
            continue
        if b < 0x80:
            if b < 0x20:
                masalah.append((f"{baris_ke}:{kolom_ke}", baris_ke,
                                f"karakter kontrol 0x{b:02X}"))
            kolom_ke += 1
            i += 1
            continue

        # UTF-8 multi-byte
        panjang = 1
        if b & 0xE0 == 0xC0:
            panjang = 2
        elif b & 0xF0 == 0xE0:
            panjang = 3
        elif b & 0xF8 == 0xF0:
            panjang = 4
        potongan = data[i:i + panjang]
        try:
            ch = potongan.decode("utf-8")
        except UnicodeDecodeError:
            masalah.append((f"{baris_ke}:{kolom_ke}", baris_ke,
                            f"byte tidak valid (0x{b:02X})"))
            i += 1
            kolom_ke += 1
            continue
        masalah.append((f"{baris_ke}:{kolom_ke}", baris_ke,
                        f"karakter non-ASCII {ch!r} (U+{ord(ch):04X})"))
        kolom_ke += 1
        i += panjang

    if not masalah:
        print(f"OK: '{path}' bersih (semua karakter ASCII, akhir baris LF).")
        return 0

    print(f"Ditemukan {len(masalah)} masalah di '{path}':")
    print()
    baris_unik = sorted({m[1] for m in masalah})
    for pos, baris, ket in masalah[:50]:
        print(f"  baris {pos:>6}  {ket}")
    if len(masalah) > 50:
        print(f"  ... dan {len(masalah) - 50} lagi")
    print()
    # tampilkan baris mentah yang bermasalah, dengan penanda
    try:
        teks = data.decode("utf-8", errors="replace").splitlines()
    except Exception:
        teks = []
    print("Baris bermasalah:")
    for b in baris_unik[:10]:
        if 1 <= b <= len(teks):
            print(f"  {b}: {teks[b - 1]}")
    print()
    print("Perbaikan: hapus/ganti karakter di atas dengan ASCII biasa.")
    return 1


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)

    if len(args) == 0:
        # stdin dipipe (bukan terminal) → jalankan seperti skrip, jangan REPL
        if not sys.stdin.isatty():
            return run_bytes(sys.stdin.buffer.read())
        repl()
        return 0
    if args[0] in ("-h", "--help"):
        print("Penggunaan: tea <file.tea>")
        print("  tea file.tea   menjalankan file")
        print("  tea check f    periksa karakter aneh di file")
        print("  tea -          menjalankan kode dari stdin")
        print("  tea            membuka REPL (tanpa argumen)")
        print("  tea-web        playground web (Flask)")
        return 0
    if args[0] in ("-v", "--version"):
        from . import __version__
        print(f"TeaScript {__version__}")
        return 0
    if args[0] == "check":
        if len(args) < 2:
            print("Penggunaan: tea check <file.tea>", file=sys.stderr)
            return 1
        return check_file(args[1])
    if args[0] == "-":
        return run_bytes(sys.stdin.buffer.read())
    return run_file(args[0])


if __name__ == "__main__":
    sys.exit(main())
