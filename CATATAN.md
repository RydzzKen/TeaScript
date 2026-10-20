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

## 4. Ide fitur yang belum dikerjakan

Lihat README bagian "Rencana ke Depan": arrow function, `map/filter/reduce`,
slicing dengan step `xs[::2]`, bytecode VM.
