#!/usr/bin/env bash
# Install TeaScript di device ini, lalu perintah `tea` bisa dipakai di mana saja.
# Pakai: bash install.sh        (opsi: bash install.sh --web  untuk +Flask)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$HERE"

WITH_WEB=0
for arg in "$@"; do
  case "$arg" in
    --web) WITH_WEB=1 ;;
    -h|--help)
      echo "Pakai: bash install.sh [--web]"
      echo "  --web   sekaligus pasang Flask untuk fitur web/tea-web"
      exit 0
      ;;
  esac
done

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Error: '$PY' tidak ditemukan. Set PYTHON=/path/ke/python3" >&2
  exit 1
fi

RECOMMENDED="."
if [ "$WITH_WEB" -eq 1 ]; then
  RECOMMENDED=".[web]"
fi

echo "Memasang TeaScript dari: $PKG"

# Coba venv milik sistem (kalau ada, lebih aman dari PEP 668)
if "$PY" -m pip install --user "$RECOMMENDED" 2>/dev/null; then
  :
elif "$PY" -m pip install "$RECOMMENDED" 2>/dev/null; then
  :
else
  echo
  echo "Gagal memasang. Kemungkinan sistem memblokir pip (PEP 668)."
  echo "Coba salah satu:"
  echo "  python3 -m venv .venv && . .venv/bin/activate && pip install \"$RECOMMENDED\""
  echo "  pipx install \"$PKG\"${WITH_WEB:+ }"
  exit 1
fi

echo
if command -v tea >/dev/null 2>&1; then
  echo "Selesai. Perintah 'tea' siap dipakai:"
  tea --version
  echo
  echo "  tea file.tea    menjalankan file"
  echo "  tea             membuka REPL"
else
  echo "Terpasang, tapi perintah 'tea' belum ada di PATH."
  echo "Tambahkan dulu folder skrip pip ke PATH, mis.:"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
