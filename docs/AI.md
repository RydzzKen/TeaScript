# TeaScript — Spesifikasi untuk AI

Tempel file ini ke AI (ChatGPT, Claude, Gemini, Copilot, dsb.) sebagai
system prompt / konteks, supaya AI bisa menulis skrip TeaScript yang benar.

Aturan emas:

1. TeaScript mirip JavaScript/Python, tapi **bukan keduanya**. Jangan
   pakai `def`, `class`, `print()` Python, `=>`, `var`, `const`, `;`.
2. Blok pakai `{ }` (bukan indentasi). Tidak ada titik koma.
3. Untuk **membuat** variabel baru wajib `let`. Menulis `x = 1` tanpa
   `let` adalah error kalau `x` belum ada.
4. Komentar hanya `//`. Tanda `#` **bukan** komentar (error).
5. Hanya ASCII di dalam kode. Jangan tulis tanda kutip pintar (“ ” ‘ ’),
   spasi tak-putus, atau huruf lebar — semua itu error.
6. Library Python diakses lewat `pyimport("nama")`, **bukan** `import`.

---

## 1. Struktur program

```tea
// komentar satu baris
let nama = "Ken"          // variabel baru wajib let
nama = "Kenji"            // assignment ulang: tanpa let
print("Halo,", nama)
```

Variabel: `number`, `string`, `boolean` (`true`/`false`), `nil`,
`list` (`[...]`), `dict` (`{kunci: nilai}`), `function`.

```tea
let angka = 42
let pecahan = 3.5
let aktif = true
let kosong = nil
let buah = ["apel", "jeruk"]
let orang = {"nama": "Ken", "umur": 20}
```

## 2. Operator

```tea
1 + 2      // 3
7 - 2      // 5
3 * 4      // 12
7 / 2      // 3.5  (pembagian selalu desimal)
7 % 3      // 1    (sisa bagi)
-5         // negatif
```

Tidak ada `**` (pangkat) — pakai `math.pow(a, b)`.

Perbandingan: `==`, `!=`, `<`, `<=`, `>`, `>=`
Logika: `and`, `or`, `not`
Keanggotaan: `x in wadah`, `x not in wadah`

Assignment gabungan: `+=`, `-=`, `*=`, `/=`, `%=`

```tea
let n = 1
n += 5     // n jadi 6
```

Ternary: `kondisi ? nilai_jika_benar : nilai_jika_salah`

```tea
let umur = 20
let label = umur >= 18 ? "dewasa" : "anak"
print(label)                 // dewasa
```

## 3. Kendali alur

```tea
let x = 15
if x > 10 {
  print("besar")
} else if x == 10 {
  print("sepuluh")
} else {
  print("kecil")
}
```

```tea
let n = 0
while n < 5 {
  n += 1
}
print(n)                     // 5

for i in range(3) {          // 0, 1, 2
  print(i)
}

for buah in ["a", "b"] {     // nilai
  print(buah)
}

for kunci in {"x": 1} {      // dict diiterasi per kunci
  print(kunci)
}

// break keluar dari loop, continue lanjut ke iterasi berikutnya
for i in range(10) {
  if i == 3 { break }
  if i % 2 == 0 { continue }
  print(i)
}
```

## 4. Fungsi

```tea
fn tambah(a, b) {
  return a + b
}
print(tambah(2, 3))          // 5

// nilai default parameter (parameter wajib harus di depan)
fn sapa(nama, sapaan = "Halo") {
  return sapaan + ", " + nama
}
print(sapa("Ken"))           // Halo, Ken
print(sapa("Ken", "Hai"))    // Hai, Ken

// fungsi anonim BELUM ada — pakai fungsi bernama
// (handler web juga fungsi bernama; lihat §10)
```

Fungsi tanpa `return` mengembalikan `nil`.
Fungsi anonim / arrow function **belum didukung** — selalu definisikan
fungsi bernama dengan `fn nama(...) { ... }`.

## 5. String

Interpolasi ala JS dengan `${ekspresi}`:

```tea
let nama = "Ken"
print("Halo, ${nama}!")                       // Halo, Ken!
print("2 + 3 = ${2 + 3}")                     // 2 + 3 = 5
```

Escape: `\n`, `\t`, `\"`, `\\`

Slicing ala Python (batas akhir eksklusif, indeks negatif dari belakang):

```tea
let s = "Halo Dunia"
s[0]        // "H"
s[0:4]      // "Halo"
s[5:]       // "Dunia"
s[-5:]      // "Dunia"
```

Hanya-baca: mengubah `s[0] = "x"` adalah error (string tidak bisa diubah).

Concatenation pakai `+`. Ulang dengan `*`:

```tea
print("ab" + "c")     // abc
print("ab" * 3)       // ababab
```

### Method string (dan juga tersedia sebagai fungsi global)

```tea
let s = "  Halo Dunia  "
s.trim()                        // "Halo Dunia"   → trim(s)
s.trim().upper()                // rantai
s.lower()                       // → lower(s)
"a,b,c".split(",")              // ["a","b","c"]  → split(s, ",")
",".join(["a","b"])             // "a,b"          → join(list, ",")
"halo".startswith("ha")         // true           → startswith(s, "ha")
"halo".endswith("lo")           // true           → endswith(s, "lo")
"a-b".replace("-", "+")         // "a+b"          → replace(s, "-", "+")
"abc".find("c")                 // 2
"abc".count("a")                // 1
"halo dunia".title()            // "Halo Dunia"
"42".isdigit()                  // true
"abc".reverse()                 // "cba"
"7".zfill(3)                    // "007"
"ab".repeat(3)                  // "ababab"
"x".center(3, "-")              // "-x-"
"hello".removeprefix("he")      // "llo"
"hello".removesuffix("lo")      // "hel"
```

Catatan: `"a,b".split(",")` mengembalikan **list**. `s.split()` tanpa
argumen memecah per karakter. `.strip()` = `.trim()`. Ada juga
`lstrip`, `rstrip`, `splitlines`, `isalpha`, `isalnum`, `isspace`,
`isupper`, `islower`, `capitalize`, `swapcase`, `rfind`, `index`,
`ljust`, `rjust`.

## 6. List dan dict

```tea
let xs = [1, 2, 3]
xs[0]            // 1
xs[-1]           // 3 (dari belakang)
xs[0:2]          // [1, 2]
xs[0] = 99       // ubah isi
len(xs)          // 3
push(xs, 4)      // tambah di akhir
pop(xs)          // buang & kembalikan yang terakhir

let d = {"nama": "Ken"}
d["nama"]        // "Ken"
d.nama           // "Ken"  (dot access juga jalan untuk dict)
d["umur"] = 20   // tambah/ubah
keys(d)          // ["nama", "umur"]
values(d)        // ["Ken", 20]
2 in xs          // true
"nama" in d      // true
```

## 7. Modul TeaScript

Tiga bentuk import:

```tea
import math                    // math.sqrt(9) — akses lewat titik
from math import sqrt          // sqrt(9) langsung
import "util.tea"              // modul dari file, nama = nama file (util)
```

Aturan:

- `import` mengikat **satu nama**; pakai dot access (`math.sqrt`).
- Nama modul diawali `_` bersifat privat, tidak ikut terekspos.
- Modul hanya dijalankan sekali (di-cache). Import melingkar dideteksi.

Modul bawaan:

| Modul | Fungsi |
| --- | --- |
| `math` | `sqrt`, `pow`, `round`, `floor`, `ceil`, `clamp`, `lerp` |
| `text` | `capitalize`, `title`, `repeat`, `replace_all`, `is_blank`, `starts_with`, `ends_with` |
| `collections` | `sum`, `product`, `reverse`, `unique`, `count`, `flatten` |
| `env` | `load`, `get`, `get_num`, `get_bool`, `wajib`, `semua`, `parse`, `reset` |

Contoh:

```tea
import math
import collections
print(math.sqrt(16))                  // 4.0
print(math.clamp(15, 0, 10))          // 10
print(collections.sum([1, 2, 3]))     // 6
print(collections.unique([1, 1, 2]))  // [1, 2]
```

### Modul `env` (baca `.env`)

**Penting:** akses lewat titik — `env.load()`, bukan `load_dotenv()`.

```tea
import env

env.load()                              // baca .env dari cwd, naik ke folder atas
let key = env.get("API_KEY", "")        // string, default "" kalau tidak ada
let port = env.get_num("PORT", 5000)    // angka
let debug = env.get_bool("DEBUG", false)// boolean (true/1/yes/on)
print(key, port, debug)
env.semua()                             // semua isi .env
// env.wajib("API_KEY")                 // error kalau variabelnya tidak ada
```

Isi `.env`:

```
# komentar
API_KEY=rahasia
PORT=5000
DEBUG=true
NAMA="Ken"            # boleh dikutip
URL=https://x.com/$PORT
```

Jangan menamai file skrip `env.tea` — menabrak modul bawaan `env`.

## 8. Interop Python

```tea
let requests = pyimport("requests")           // import library Python
let json = pyimport("json")

print(json.dumps({"a": 1}))
print(math_hasil)                             // objek Python apa pun bisa dipakai

// atribut objek Python: pakai titik, sama seperti Python
let r = requests.get("https://example.com")
print(r.status_code)
print(r.json()["key"])

// keyword argument Python ditulis "let _nama = nilai"
print(json.dumps({"a": 1}, let _indent = 2))
let r2 = requests.post(url, let _json = data, let _headers = h)
```

`pyimport` memakai cache Python; modul yang sama tidak diimpor dua kali.
Kalau gagal: `Error: pyimport(): modul Python 'x' tidak ditemukan`.

**Keyword argument** aturannya: diawali garis bawah, ditulis dalam
pemanggilan. `foo(let _end = "")` di TeaScript → `foo(end="")` di Python.

## 9. Fungsi bawaan

| Fungsi | Keterangan |
| --- | --- |
| `print(...)` | cetak. Ada kwargs: `print("x", let _end = "", let _sep = ",", let _flush = true)` |
| `len(x)` | panjang string/list/dict |
| `input(prompt?)` | baca satu baris dari pengguna (mengembalikan string) |
| `str(x)`, `num(x)` | ubah tipe |
| `type(x)` | `"number"`, `"string"`, `"boolean"`, `"nil"`, `"list"`, `"dict"`, `"function"` |
| `push(list, ...nilai)`, `pop(list)` | list: tambah/buang di akhir |
| `keys(dict)`, `values(dict)` | isi dict |
| `range(n)` / `range(a, b)` / `range(a, b, step)` | deret (batas akhir eksklusif) |
| `includes(wadah, x)` | sama dengan `x in wadah` |
| `abs(x)`, `min(...)`, `max(...)` | angka (min/max boleh satu list) |
| `upper`, `lower`, `trim`, `split`, `join` | string (lihat juga method di §5) |
| `startswith(s, x)`, `endswith(s, x)`, `replace(s, a, b)` | string |
| `pyimport(nama)` | muat modul Python |
| `getenv(nama, default?)` | variabel lingkungan OS |
| `setenv(nama, nilai)` | set variabel lingkungan |
| `error(pesan)` | hentikan program dengan pesan sendiri (exit code 1) |
| `Web.app()` | server web (lihat §10) |

## 10. Web (Flask)

`Web` sudah bawaan — **tidak** lewat `pyimport("flask")`.

Handler adalah **fungsi bernama** (bukan anonim), didaftarkan dengan
`app.get(path)(nama_fungsi)` atau `app.route(path)(nama_fungsi)`:

```tea
let app = Web.app()

fn home() {
  return "Halo dari TeaScript!"
}

fn user(nama) {
  return {"nama": nama, "salam": "Halo " + nama}
}

fn kirim() {
  return {"status": "ok"}
}

app.route("/")(home)
app.route("/api/user/<nama>")(user)
app.route("/kirim")(kirim)          // atau app.post("/kirim")(kirim)

app.run()          // default port 5000, host 127.0.0.1
```

Parameter route dari URL jadi argumen fungsi (`<nama>` → argumen
`nama`). Nilai `return`:

- string → teks biasa
- dict/list → otomatis jadi JSON
- `nil` → 204, `true`/`false` → 200/500, angka → teks

Jalankan: `tea-web file.tea --port 5000` (Flask harus terpasang:
`pip install "teascript[web]"`).

## 11. Cara menjalankan

```bash
tea file.tea            # jalankan file
teascript file.tea      # nama alternatif (kalau 'tea' bentrok)
tea                     # REPL
tea -                   # baca kode dari stdin
echo 'print("hi")' | tea
tea check file.tea      # periksa karakter aneh (non-ASCII, CRLF, BOM)
tea info                # versi & lokasi paket
tea-web file.tea        # jalankan sebagai server web
```

## 12. Error

Format: `Error (baris N): pesan` (syntax error menyertakan kolom).
Exit code 1 saat gagal, 0 saat sukses. Error ditulis ke stderr.

```
Error (baris 2): variabel 'y' belum dideklarasikan
Error (baris 2, kolom 1): ekspresi tidak lengkap (menemukan akhir file)
Error (baris 3): karakter tidak dikenal: '#'
```

Pesan error berbahasa Indonesia, tapi **kata kunci bahasa tetap Inggris**.

---

## 13. Contoh lengkap

### FizzBuzz

```tea
for i in range(1, 21) {
  if i % 15 == 0 {
    print("FizzBuzz")
  } else if i % 3 == 0 {
    print("Fizz")
  } else if i % 5 == 0 {
    print("Buzz")
  } else {
    print(i)
  }
}
```

### Chatbot REST API (Gemini)

```tea
import env

env.load()
let API_KEY = env.get("GEMINI_API_KEY", "")
if API_KEY == "" {
  print("API key belum ada. Buat .env berisi GEMINI_API_KEY=xxxxx")
  error("GEMINI_API_KEY kosong")
}

let requests = pyimport("requests")
let model = env.get("GEMINI_MODEL", "gemini-flash-lite-latest")
let url = "https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${API_KEY}"

while true {
  let user = input("You : ")
  if trim(user) == "" or lower(trim(user)) == "exit" { break }

  let payload = {"contents": [{"parts": [{"text": user}]}]}
  let header = {"Content-Type": "application/json"}
  let r = requests.post(url, let _json = payload, let _headers = header)

  if r.status_code != 200 {
    print("Error HTTP:", r.status_code)
    continue
  }
  let data = r.json()
  print("AI  : ${data["candidates"][0]["content"]["parts"][0]["text"]}")
}
```

### Server web

```tea
let app = Web.app()

let catatan = []

fn home() {
  return "TeaNotes — kirim catatan ke POST /catatan/<isi>"
}

fn tambah_catatan(isi) {
  push(catatan, isi)
  return {"jumlah": len(catatan)}
}

fn daftar() {
  return catatan
}

app.route("/")(home)
app.route("/catatan/<isi>")(tambah_catatan)
app.route("/catatan")(daftar)

app.run()
```

### Baca konfigurasi & file

```tea
import env

env.load()
let nama = env.get("NAMA", "tanpa nama")
let port = env.get_num("PORT", 5000)
let debug = env.get_bool("DEBUG", false)

print("Nama : ${nama}")
print("Port : ${port} (${type(port)})")
print("Debug: ${debug} (${type(debug)})")
```

---

## 14. Kesalahan yang sering dibuat AI

| Salah | Benar |
| --- | --- |
| `def f(x):` | `fn f(x) { ... }` |
| `x = 1` (pembuatan baru) | `let x = 1` |
| `x++` / `x--` | `x += 1` / `x -= 1` |
| `i++;` (titik koma) | tidak ada `;` sama sekali |
| `# komentar` | `// komentar` |
| `2 ** 3` | `math.pow(2, 3)` |
| `import requests` | `let requests = pyimport("requests")` |
| `load_dotenv()` | `import env` lalu `env.load()` |
| `s.upper` | `s.upper()` (harus dipanggil) |
| `"abc".length` | `len("abc")` |
| `arr.append(1)` | `push(arr, 1)` |
| `arr.length` | `len(arr)` |
| `True` / `False` / `None` | `true` / `false` / `nil` |
| `console.log(x)` | `print(x)` |
| `x === y` | `x == y` |
| `let x = 1;` | `let x = 1` |
| `for i in range(3):` (indentasi) | `for i in range(3) { }` |
| `f(x, end="")` | `f(x, let _end = "")` |
| `dict.get("k")` | `d["k"]` atau `d.k` |
| `"a" + 1` | `"a" + str(1)` (tipe harus cocok) |
| `let f = fn(x) { ... }` (anonim) | fungsi bernama: `fn f(x) { ... }` |
| `app.get("/", fn() {...})` | `app.route("/")(home)` dengan `fn home() {}` |
