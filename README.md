# TeaScript ☕

TeaScript adalah bahasa skrip kecil bergaya **JavaScript/Python**, diimplementasikan murni di Python tanpa dependensi eksternal.
Dirancang sebagai proyek belajar bagaimana sebuah bahasa pemrograman bekerja: **lexer → parser → evaluator**.

```tea
let nama = "Ken"
let sapaan = "Halo, ${nama}!"
print(len(sapaan) > 5 ? sapaan : "singkat sekali")
```

## Fitur

- Variabel `let`, assignment biasa dan gabungan (`+=`, `-=`, `*=`, `/=`, `%=`)
- Tipe: number, string, boolean, `nil`, list, dictionary, fungsi
- Kendali alur: `if / else if / else`, `while`, `for ... in`, `break`, `continue`
- Ternary ala JS: `kondisi ? a : b`
- Fungsi dengan closure dan `return`
- String interpolasi ala JS: `"Halo, ${nama}!"`
- Slicing ala Python: `xs[1:3]`, `s[:5]`, `xs[-2:]`, `xs[:]`
- Operator keanggotaan: `x in daftar`, `x not in daftar`
- **Modul**: `import math`, `from collections import sum`, dot access `math.sqrt(2)`
- **Interop Python**: `let m = pyimport("math")` → pakai library Python apa pun
- **Bikin web**: `Web.app()` untuk server Flask yang handler-nya fungsi TeaScript
- 20 fungsi bawaan + 3 modul stdlib (`math`, `text`, `collections`)
- Error dengan posisi **baris:kolom**, REPL, dan 135 test

## Instalasi

### Cara tercepat: satu perintah

```bash
git clone <repo> TeaScript && cd TeaScript   # atau salin foldernya ke device lain
bash install.sh                                # cukup: bash install.sh
bash install.sh --web                          # + Flask (fitur tea-web)
```

Setelah itu perintah `tea` bisa dipakai dari folder mana saja:

```bash
tea tes.tea        # jalankan file
tea                # buka REPL
tea --version
```

Kalau `tea` belum terbaca, tambahkan folder skrip pip ke PATH
(`export PATH="$HOME/.local/bin:$PATH"`) atau pakai venv:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install ".[web]"
tea tes.tea
```

### Cara manual (pip)

```bash
python3 -m pip install .            # CLI saja
python3 -m pip install ".[web]"     # + web (Flask)
tea file.tea
tea --version
```

Bisa juga lewat module: `python3 -m teascript file.tea`

### Pindah ke device lain

TeaScript murni Python, **tanpa dependensi wajib** (Flask hanya untuk fitur web).
Dua cara memindahkan:

```bash
# A. dari folder sumber (paling gampang)
bash install.sh

# B. bikin paket, lalu pasang paketnya di device lain
python3 -m build                 # hasilkan dist/*.whl
pip install dist/teascript-0.3.0-py3-none-any.whl
```

> Catatan: `pyimport("requests")` dan `Web.app()` butuh modul Python terkait
> terpasang di device itu (`pip install requests`, `pip install flask`).
> Fitur inti TeaScript jalan tanpa keduanya.

## Contoh Cepat

```tea
// Fungsi + loop + compound assignment
fn faktorial(n) {
  let hasil = 1
  for i in range(2, n + 1) {
    hasil *= i
  }
  return hasil
}

print(faktorial(5))                    // 120
print(10 > 5 ? "benar" : "salah")      // benar — ternary
```

Lebih lengkap ada di folder [`examples/`](examples/): `fizzbuzz.tea`, `statistik.tea`, `strings.tea`, `belanja.tea`.

---

## Referensi Sintaks

### Variabel

```tea
let x = 10
x = 20          // assignment
x += 5          // compound: 25 (juga -=, *=, /=, %=)
xs[0] *= 2      // compound lewat indeks
```

### Tipe data

| Tipe      | Contoh                     |
| --------- | -------------------------- |
| number    | `42`, `3.14`               |
| string    | `"halo"`, `'hai'`          |
| boolean   | `true`, `false`            |
| nil       | `nil`                      |
| list      | `[1, 2, 3]`                |
| dict      | `{nama: "budi", umur: 20}` |
| function  | `fn f() { }`               |

### Operator

| Kelompok    | Operator                                        |
| ----------- | ----------------------------------------------- |
| Aritmatika  | `+` `-` `*` `/` `%`                             |
| Perbandingan| `==` `!=` `<` `>` `<=` `>=`                     |
| Logika      | `and` `or` `not` (short-circuit)                |
| Keanggotaan | `in`, `not in`                                  |
| Lainnya     | unary `-`, ternary `? :`, indexing `x[i]`, slice `x[a:b]` |

Catatan:
- `+` dengan salah satu string → penggabungan string (`1 + "a"` → `"1a"`)
- `/` selalu menghasilkan desimal, seperti Python (`6 / 3` → `2.0`)
- `true`/`false` tidak pernah sama dengan `1`/`0`

### Kendali alur

```tea
if x > 10 {
  print("besar")
} else if x > 5 {
  print("sedang")
} else {
  print("kecil")
}

while i < 3 {
  i += 1
  if i == 2 { continue }   // lompat ke iterasi berikutnya
  if i == 5 { break }      // hentikan loop
}

for item in [1, 2, 3] { print(item) }   // list
for c in "abc" { print(c) }             // string → karakter per huruf
for k in {a: 1} { print(k) }            // dict → key

let sapaan = umur > 17 ? "dewasa" : "anak"   // ternary
```

Yang bisa diiterasi `for ... in`: **list, string, dict** (dict → key-nya).

### Fungsi

```tea
fn tambah(a, b) {
  return a + b
}
print(tambah(2, 3))   // 5

fn tanpaNilai() { return }   // return tanpa nilai → nil
```

### String

```tea
let nama = "Ken"

// Interpolasi ${...} — bebas ekspresi di dalamnya
let s = "Halo, ${nama}! 1+1=${1 + 1}"    // "Halo, Ken! 1+1=2"

// Slicing (batas negatif dihitung dari akhir, di-clamp ke panjang)
print(s[0:4])      // "Halo"
print(s[-4:])      // "Ken!"
print(s[:])        // seluruh string
```

### List & dict

```tea
let xs = [1, 2, 3, 4, 5]
print(xs[0])       // 1
print(xs[1:3])     // [2, 3]
print(xs[-2:])     // [4, 5]
push(xs, 6)        // [1, 2, 3, 4, 5, 6]
print(pop(xs))     // 6
print(3 in xs)     // true

let d = {nama: "budi"}
d["umur"] = 20
print(d["nama"])   // budi
print(keys(d))     // ["nama", "umur"]
```

### Komentar

```tea
// komentar sampai akhir baris
```

---

## Modul & Import

Sama seperti Python: `import` memuat file `.tea` lain dan mengikatnya ke satu nama, anggota diakses lewat titik.

```tea
import math                    // cari math.tea (lihat urutan pencarian)
print(math.sqrt(2))            // 1.4142135623730951
print(math.PI)                 // 3.141592653589793

from collections import sum    // ambil langsung ke lingkup sekarang
print(sum([1, 2, 3]))          // 6

import "lib/konversi.tea"      // path eksplisit; nama binding = nama file
print(konversi.c2f(100))       // 212.0
```

Aturan:

- **Urutan pencarian** `import nama`: folder file yang sedang jalan → stdlib `teascript/modules/` → folder di environment `TEASCRIPT_PATH` (dipisah `:`).
- **Semua nama publik** di top-level modul menjadi ekspor. Nama yang diawali `_` bersifat privat dan tidak bisa diakses pembeli.
- Modul **dieksekusi sekali**, hasilnya di-cache (seperti Python).
- **Import melingkar** terdeteksi dan memberi error berantai: `import melingkar: a.tea -> b.tea -> a.tea`.
- Error di dalam modul menyebut nama file modulnya.
- Dot access juga berlaku untuk dict: `d.nama` sama dengan `d["nama"]`.

### Stdlib (ditulis dalam TeaScript)

| Modul | Anggota |
| ----- | ------- |
| `math` | `PI`, `E`, `sqrt`, `pow`, `round`, `floor`, `ceil`, `clamp`, `lerp` |
| `text` | `capitalize`, `title`, `repeat`, `replace_all`, `is_blank`, `starts_with`, `ends_with` |
| `collections` | `sum`, `product`, `reverse`, `unique`, `count`, `flatten` |

Bikin modul sendiri cukup simpan `namamu.tea` di folder yang sama dengan script, lalu `import namamu`.

---

## Interop Python (pyimport)

`pyimport("nama_modul")` memuat modul Python apa pun yang terpasang di sistem Python kamu:

```tea
let m = pyimport("math")
print(m.sqrt(144))             // 12.0 — method Python dipanggil langsung

let json = pyimport("json")
print(json.dumps({a: 1}))      // {"a": 1} — dict TeaScript = dict Python

let re = pyimport("re")
if re.match("\\d+", "abc123") {
  print("ada angka")
}
```

Catatan:

- Nilai Python yang masuk dipakai apa adanya: string/angka/list/dict cocok otomatis; objek lain (mis. `Response` dari `requests`) jadi nilai opak yang bisa diberi atribut (`resp.status`, `resp.headers`).
- Atribut objek Python bisa dibaca **dan ditulis**: `obj.foo`, `obj.foo = 1`.
- Fungsi Python yang di-return bisa dipanggil langsung: `re.match(...)`.
- `type(objek_python)` mengembalikan nama kelasnya (mis. `"module"`).
- Karena ini menjalankan Python penuh, `pyimport` hanya untuk kode yang kamu percaya.

---

## Fungsi Bawaan

### Umum

| Fungsi | Keterangan |
| ------ | ---------- |
| `print(...)` | cetak nilai, dipisah spasi |
| `input(prompt)` | baca input pengguna (→ string) |
| `len(x)` | panjang string/list/dict |
| `str(x)` | ubah ke string |
| `num(x)` | ubah ke number (`"7"` → `7`) |
| `type(x)` | tipe nilai: `"number"`, `"string"`, `"boolean"`, `"nil"`, `"list"`, `"dict"`, `"function"` |

### List & dict

| Fungsi | Keterangan |
| ------ | ---------- |
| `push(list, ...)` | tambahkan elemen, mengembalikan list-nya |
| `pop(list)` | hapus & ambil elemen terakhir |
| `keys(dict)` | daftar key |
| `values(dict)` | daftar nilai |

### Angka

| Fungsi | Keterangan |
| ------ | ---------- |
| `range(n)` / `range(a, b)` / `range(a, b, step)` | deret angka bulat, batas akhir eksklusif |
| `abs(x)` | nilai mutlak |
| `min(...)` / `max(...)` | nilai terkecil/terbesar (boleh satu argumen list) |

### String

| Fungsi | Keterangan |
| ------ | ---------- |
| `upper(s)` / `lower(s)` | huruf besar/kecil |
| `trim(s)` | hapus spasi di ujung |
| `split(s, pemisah)` | string → list (`pemisah ""` → per karakter) |
| `join(list, pemisah)` | list → string |

### Keanggotaan

| Fungsi | Keterangan |
| ------ | ---------- |
| `includes(wadah, x)` | sama dengan `x in wadah` |

---

## Catatan Semantik

- **Truthiness**: `nil`, `false`, `0`, dan `""` dianggap salah; sisanya benar.
- **Scope**: variabel mengikuti lingkup blok fungsi; `let` di dalam fungsi tidak mengubah variabel luar, tapi assignment ke variabel luar tetap berlaku (closure).
- **Key dict** harus tipe yang bisa disimpan (string, number, boolean, nil) — error jelas jika tidak.
- **Error** selalu menyertakan posisi, mis. `Error (baris 3, kolom 8): variabel 'x' belum dideklarasikan`.

## Bikin Web dengan TeaScript

TeaScript bisa menjalankan **server web sendiri** lewat `pyimport("flask")`, persis seperti Flask di Python. Jalankan file `.tea` sebagai server:

```bash
tea-web examples/web.tea --port 5000
```

Isi `examples/web.tea`:

```tea
let app = Web.app("teascript")

fn home() { return "<h1>Halo dari TeaScript</h1>" }
fn sapa(nama) { return "Halo, ${nama}!" }
fn info() { return {nama: "TeaScript", versi: "0.3.0"} }   // dict → JSON

app.route("/")(home)
app.route("/sapa/<nama>")(sapa)
app.route("/info")(info)
app.route("/usia/<int:usia>")(umur)   // <int:...> otomatis jadi angka

app.run()
```

Yang perlu diketahui:

- **`Web.app(nama)`** — pembungkus ringan di atas Flask. Nama route diambil dari nama fungsi (`fn home` → endpoint `home`).
- **Handler TeaScript benar-benar callable dari Python**, jadi framework apa pun (`flask`, `fastapi`) bisa memakai fungsi TeaScript sebagai handler.
- **Nilai balik** diterjemahkan otomatis: string/bytes → teks, dict/list → JSON, angka → teks, `nil` → `204 No Content`.
- **`app.route(rule)` dua kali untuk rule sama** → error, tidak diam-diam tertimpa.
- Ingin Flask mentah? Pakai `let flask = pyimport("flask")` lalu `flask.Flask(...)` seperti biasa.

### Server API + playground

Selain menjalankan file, ada server bawaan untuk menjalankan kode lewat HTTP:

```bash
tea-web              # playground + API di http://127.0.0.1:5000
```

- `POST /api/run` — eksekusi kode: `{"source": "...", "inputs": ["jawaban"]}`
  → `{"ok": true, "output": "...", "error": null}`
- `GET /api/examples` dan `GET /api/example/<nama>` — daftar/isi contoh program
- `GET /` — info API (halaman playground UI belum dibuat)
- `input()` di web dijawab dari field `inputs`, jadi server tidak pernah menunggu stdin.

## Menjalankan Test

```bash
python3 -m pytest
```

141 test menutup lexer, parser, evaluator, builtins, sistem modul, pyimport, web (termasuk server HTTP sungguhan), packaging, dan CLI.

## Struktur Proyek

```
TeaScript/
├── tea.py              # entry point CLI (python3 tea.py)
├── webapp.py           # entry point server web
├── install.sh          # pemasang satu perintah (bash install.sh)
├── pyproject.toml      # packaging (perintah `tea`, `tea-web`)
├── .gitignore
├── teascript/
│   ├── lexer.py        # teks → token (string, escape, interpolasi)
│   ├── token.py        # definisi token & keyword
│   ├── parser.py       # token → AST (recursive descent)
│   ├── ast_nodes.py    # definisi node AST
│   ├── evaluator.py    # eksekusi AST + builtins + modul + web
│   ├── errors.py       # error ber-posisi
│   ├── repl.py         # REPL interaktif
│   ├── web.py          # server Flask (API + tea-web)
│   ├── cli.py          # argumen command line
│   └── modules/        # stdlib TeaScript: math, text, collections
├── examples/           # contoh program .tea
└── tests/              # unit test
```

## Rencana ke Depan

- [ ] Fungsi anonim / arrow function `() => ...`
- [ ] `map`, `filter`, `reduce` (higher-order function)
- [ ] Slicing dengan step `xs[::2]`
- [ ] Bytecode VM sebagai alternatif evaluator
