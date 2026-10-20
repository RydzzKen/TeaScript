# Catatan Proyek

Dokumen kerja TeaScript: keputusan yang bisa berubah, pekerjaan yang ditunda, dan cara melanjutkannya.
Diperbarui: 20 Oktober 2026.

## 1. Antislop (filter kualitas UI) — DITANGGUHKAN

Status: **belum dipakai, tidak ada yang diinstall**.
Alasan: fokus proyek sekarang ke terminal, jadi belum ada pekerjaan UI yang butuh filter ini.
Mode (DURING/AFTER) belum dipilih.

Kalau berubah pikiran, jalankan langkah ini di sesi berikutnya:

1. **Pilih mode** saat ditanya antislop:
   - **DURING** = aturan diterapkan saat menulis UI (mencegah tampilan generik sejak awal).
   - **AFTER** = UI dibuat dulu, lalu diaudit jadi daftar temuan bernomor, baru dipilih yang diperbaiki.
2. **Install skill tambahan.** Rilis lokal sudah ada di mesin dan versinya cocok dengan core (3.2.21):
   - Core: `~/.config/opencode/skills/antislop/SKILL.md`
   - Skill: `~/.npm/_npx/1f5c8ecd5237e33b/node_modules/antislop-ai/skills/`
     (isi: `antislop-ui`, `antislop-copywriting`, `antislop-human`, `antislop-layoutmobile`, `antislop-code`)
   - Jalankan: salin folder skill yang dipilih ke `skills/<nama>/` di samping core, atau jalankan ulang `npx antislop-ai`.
   - Jangan campur folder dari rilis berbeda.
   - Yang paling relevan untuk proyek ini: **`antislop-ui`**.
3. **Tambahkan blok pointer** di akhir `AGENTS.md` (file itu belum ada di project, buat baru).
   Format blok ada di `SKILL.md` core, bagian "First-Run Install Wizard" langkah 5.
4. Kalau memilih core saja (tanpa skill), cukup ikuti isi `SKILL.md` core sebagai filter.

Tidak ada yang diinstall sampai langkah di atas dijalankan.

## 2. Web (server di dalam TeaScript) — SELESAI

TeaScript bisa bikin server web sendiri, seperti Flask:

```tea
let app = Web.app("teascript")
fn home() { return "<h1>Halo</h1>" }
app.route("/")(home)
app.run()
```

Jalankan: `tea-web examples/web.tea --port 5000`

Yang dibuat:

- `Web.app(nama)` di evaluator (`_install_web`): route dari nama fungsi handler,
  dict/list → JSON, angka → teks, `nil` → 204, route duplikat → error.
- `Function.__call__` + `Evaluator.invoke`/`to_python`: fungsi TeaScript callable dari Python.
- Keyword argument: parameter boleh pakai keyword Python (`fn f(as_text)`) dan
  pemanggilan bisa `f(let _as_text = true)`.
- `TEASCRIPT_NO_BLOCK=1` mencegah `app.run()` memblokir (dipakai test).
- `tea-web <file.tea>` menjalankan file sebagai server; `--port`/`--host`
  diteruskan lewat `TEASCRIPT_PORT`/`TEASCRIPT_HOST`.

Sisa (kalau mau): halaman playground web (nilai tambah buat belajar).

## 3. Publikasi — SEBAGIAN SELESAI

Repo publik: **https://github.com/RydzzKen/TeaScript** (branch `main`).

Sudah:

- Git repo lokal + commit awal (`0.3.0`), 38 file, file pribadi `tes.tea` tidak ikut.
- `LICENSE` MIT, metadata `pyproject.toml` lengkap (URL repo, classifier).
- GitHub Actions: `.github/workflows/tests.yml` (test di 3 versi Python + build),
  `.github/workflows/publish.yml` (rilis otomatis ke PyPI via Trusted Publishing).
- Terbukti bisa: `pip install "teascript @ git+https://github.com/RydzzKen/TeaScript.git"`.

Belum (butuh akun/tindakan pemilik):

1. **Rilis PyPI** supaya `pip install teascript` (nama masih bebas di PyPI).
   Dua jalur:
   - **Trusted Publishing** (disarankan, tanpa token): di pypi.org → Account →
     Publishing → tambah *pending publisher* dengan Owner `RydzzKen`,
     Repository `TeaScript`, Workflow `publish.yml`, Environment `pypi`.
     Lalu buat Release di GitHub → paket terbit otomatis.
   - **Manual**: `python -m build` lalu `python -m twine upload dist/*`
     (butuh API token dari pypi.org).
2. Ganti identitas commit (`TeaScript contributors <teascript@users.noreply.github.com>`)
   kalau ingin pakai nama/email sendiri: `git commit --amend --reset-author`.
3. Setelah terbit: tambah badge PyPI + `pip install teascript` di README (sudah ada,
   tinggal aktif).

## 4. Modul `env` + default parameter — SELESAI (permintaan: `from dotenv import load_dotenv`)

Latar: `from dotenv import load_dotenv` tidak bisa di TeaScript (`from`/`import`
hanya mencari file `.tea`, bukan modul Python), dan `python-dotenv` punya masalah
`find_dotenv()` saat dipanggil dari TeaScript (ia menebak lewat stack frame dan
melihat `evaluator.py`, bukan file `.tea`).

Keputusan: **bikin sendiri** — modul `env` bawaan, murni TeaScript.

Yang dibuat:

- `teascript/modules/env.tea`: `load`, `get`, `get_num`, `get_bool`, `wajib`,
  `semua`, `parse`, `reset`. Dukung komentar `#`, kutip, `export`, interpolasi
  `${VAR}`/`$VAR`, cari `.env` naik ke folder induk. Tanpa paket Python tambahan.
- Builtin baru: `error(...)`, `getenv(nama, default)`, `setenv(nama, nilai)`.
- Fitur bahasa baru: **nilai default parameter** — `fn sapa(nama, sapaan = "Halo")`.
  Parameter ber-default wajib setelah parameter wajib; dievaluasi tiap panggilan.
- Perbaikan: file yang sedang berjalan tidak boleh `import` dirinya sendiri
  (mis. `examples/env.tea` → ambil modul stdlib `env`), dan impor melingkar
  murni tetap memberi pesan `import melingkar: a.tea -> b.tea -> a.tea`.
- Test: `tests/test_features_env.py` (22 test). Total suite: **163 lulus**.
- Contoh: `examples/env.tea`.

Catatan: `pyimport("dotenv")` tetap bisa dipakai, tapi `load_dotenv()` tanpa
argumen tidak bekerja (akar masalah di `find_dotenv`). Pakai `import env` saja.

## 5. `tea check` + deteksi karakter aneh — SELESAI

Latar: di Termux muncul `karakter tidak dikenal: '.'`. Ternyata penyebabnya
karakter non-ASCII yang ikut saat copy-paste (spasi tak-putus, kutip pintar,
atau karakter lebar-penuh yang terlihat mirip ASCII).

Yang dibuat:

- Lexer menolak **identifier non-ASCII** (mis. `ｎ` lebar-penuh) supaya tidak
  diam-diam jadi variabel berbeda dari yang dikira.
- Pesan error karakter aneh kini menyebut jenisnya + kode `U+XXXX` + saran
  (mis. "ini spasi tak-putus, biasanya ikut saat copy-paste").
- Perintah baru **`tea check <file.tea>`**: daftar baris:kolom tiap karakter
  non-ASCII, CRLF, BOM, byte tidak valid; lalu menampilkan baris bermasalah.
- Test: `tests/test_cli.py` bertambah (7 test). Total suite: **171 lulus**.
- README: bagian **Troubleshooting: "karakter tidak dikenal"**.

## 6. Perintah `teascript` + `tea info` — SELESAI

Latar: di Termux, `tea check`/`tea --version` sempat memberi *"file 'check'
tidak ditemukan"*. Ternyata `tea` di PATH bukan versi yang baru dipasang
(nama `tea` terlalu umum, mudah ditutupi program lain / cache shell lama).

Yang dibuat:

- Perintah alternatif **`teascript`** dan **`teascript-web`** di `pyproject.toml`
  (kode sama dengan `tea`/`tea-web`; kalau `tea` bentrok, pakai yang ini).
- Perintah baru **`tea info`**: tampilkan versi, lokasi paket, python, dan
  **peringatan** kalau `tea` di PATH bukan milik paket ini.
- `--help` menyebut `info` + catatan sinonim `tea`/`teascript`.
- Contoh **`examples/gemini.tea`**: chatbot Gemini via `pyimport("requests")`,
  API key dibaca dari `.env` (tidak ditulis di file).
- `examples/env.tea` → `examples/konfigurasi.tea` (nama lama menabrak modul
  stdlib `env`; ketemu saat menguji `examples/gemini.tea`).
- Test baru: alias di pyproject, `tea info`, contoh tidak bentrok nama modul
  stdlib. Total suite: **178 lulus**.
- README: bagian **Troubleshooting: perintah `tea` tertukar** + contoh Gemini.

## 7. Method string (`s.upper()`) — SELESAI

Permintaan: setelah `env.load()` (yang pakai titik) terasa seperti Python,
user bertanya apakah ada `s.upper()`, `s.strip()`, `s.split()`, dst.
Saat itu **belum ada** — hanya bentuk fungsi global `upper(s)`, dan
`s.upper` memberi error menyesatkan `indeks string harus angka bulat`.

Yang dibuat (pilihan "keduanya" — method **dan** fungsi global):

- Method string ala Python/JS: `s.upper()`, `s.lower()`, `s.trim()`,
  `s.split(",")`, `s.startswith("x")`, `s.endswith("x")`, `s.replace(a,b)`,
  `s.find`, `s.count`, `s.title`, `s.isdigit`, `s.reverse`, `s.repeat`,
  `s.zfill`, `s.center/ljust/rjust`, `s.removeprefix/removesuffix`, dst.
- Bisa dirantai: `"  x  ".trim().upper()`, `"a,b".split(",")[1].upper()`.
- Fungsi global baru: `startswith`, `endswith`, `replace`. Yang lama
  (`upper/lower/trim/split/join`) tetap jalan — tidak ada skrip yang rusak.
- `split(s)` tanpa pemisah → per karakter (sebelumnya pemisah wajib).
- Implementasi: `BoundMethod` + `StringView` di `evaluator.py`. Subclass `str`
  tidak dipakai karena `str` immutable (tidak bisa diberi atribut); jadi
  `StringView` adalah pembungkus tipis yang menyerahkan operasi lain ke
  string aslinya, sehingga hasil method tetap bisa dibandingkan/digabung
  dan dipakai sebagai key dictionary.
- Error lebih menolong: `s.tidakada()` menyebut semua method yang tersedia;
  `s.upper_()` menyarankan versi tanpa garis bawah.
- Tests: +8 (method, rantai, hasil tetap string, error). Total **186 lulus**.
- README: bagian String ditulis ulang + daftar fitur; `examples/strings.tea`
  diperluas jadi peraga method.

## 8. Ide fitur yang belum dikerjakan

Lihat README bagian "Rencana ke Depan": arrow function, `map/filter/reduce`,
slicing dengan step `xs[::2]`, bytecode VM.
