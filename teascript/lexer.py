"""Tahap 1: Lexer mengubah teks menjadi list Token."""

from .token import (
    Token, NUMBER, STRING, INTERP, IDENT, KEYWORD, OP, PUNCT, EOF,
    KEYWORDS, TWO_CHAR_OPS, ONE_CHAR_OPS, PUNCTUATION,
)
from .errors import SyntaxErrorTea

# Escape sequence yang didukung di dalam string
ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "\\": "\\",
    '"': '"',
    "'": "'",
    "0": "\0",
    "$": "$",
}


class Lexer:
    def __init__(self, source, line_offset=0, column_offset=0):
        self.source = source
        self.pos = 0
        self.line = 1 + line_offset
        self.column = 1 + column_offset
        self.tokens = []

    def error(self, msg):
        raise SyntaxErrorTea(msg, self.line, self.column)

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return "\0"

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self):
        while self.pos < len(self.source):
            ch = self.peek()

            # Spasi & newline
            if ch in " \t\r\n":
                self.advance()
                continue

            # Komentar //
            if ch == "/" and self.peek(1) == "/":
                while self.pos < len(self.source) and self.peek() != "\n":
                    self.advance()
                continue

            # Angka
            if ch.isdigit():
                self.read_number()
                continue

            # String
            if ch in "\"'":
                self.read_string()
                continue

            # Identifier / keyword (hanya ASCII, supaya karakter "mirip"
            # seperti ｎ lebar-penuh tidak diam-diam jadi variabel berbeda)
            if ch.isalpha() or ch == "_":
                if not ch.isascii():
                    self.error(self._pesan_karakter_aneh(ch))
                self.read_ident()
                continue

            # Operator dua karakter
            two = ch + self.peek(1)
            if two in TWO_CHAR_OPS:
                line, col = self.line, self.column
                self.advance()
                self.advance()
                self.tokens.append(Token(OP, two, line, col))
                continue

            # Operator satu karakter
            if ch in ONE_CHAR_OPS:
                line, col = self.line, self.column
                self.advance()
                self.tokens.append(Token(OP, ch, line, col))
                continue

            # Punctuasi
            if ch in PUNCTUATION:
                line, col = self.line, self.column
                self.advance()
                self.tokens.append(Token(PUNCT, ch, line, col))
                continue

            self.error(self._pesan_karakter_aneh(ch))

        self.tokens.append(Token(EOF, None, self.line, self.column))
        return self.tokens

    def _pesan_karakter_aneh(self, ch):
        """Pesan jelas untuk karakter yang tidak dikenal lexer.

        Kalau karakter tampak mirip karakter biasa (mis. non-breaking space,
        zero-width space, tanda kutip 'pintar'), jelaskan asalnya supaya
        tidak bingung 'kenapa . ini error'.
        """
        mirip = {
            "\u00a0": "spasi tak-putus (non-breaking space)",
            "\u200b": "zero-width space",
            "\u200c": "zero-width non-joiner",
            "\u200d": "zero-width joiner",
            "\ufeff": "byte-order mark (BOM)",
            "\u2018": "tanda kutip satu 'pintar'",
            "\u2019": "tanda kutip satu 'pintar'",
            "\u201c": "tanda kutip dua 'pintar'",
            "\u201d": "tanda kutip dua 'pintar'",
            "\u2013": "tanda hubung en-dash",
            "\u2014": "tanda hubung em-dash",
            "\u2026": "elipsis (…)",
            "\u00d7": "tanda kali (×)",
            "\u2212": "tanda minus (−)",
            "\uff0e": "titik lebar penuh (．)",
            "\uff0f": "garis miring lebar penuh (／)",
            "\u3002": "titik ideografik (。)",
        }
        if ch in mirip:
            return (f"karakter tidak dikenal: {ch!r} — ini {mirip[ch]} "
                    f"(kode U+{ord(ch):04X}), biasanya ikut saat copy-paste. "
                    f"Ganti dengan karakter ASCII biasa.")
        if 32 <= ord(ch) < 127:
            return f"karakter tidak dikenal: {ch!r}"
        return (f"karakter tidak dikenal: {ch!r} (kode U+{ord(ch):04X}) — "
                f"bukan karakter ASCII, mungkin ikut saat copy-paste.")

    def read_number(self):
        line, col = self.line, self.column
        start = self.pos
        while self.peek().isdigit():
            self.advance()
        # desimal opsional
        if self.peek() == "." and self.peek(1).isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
        text = self.source[start:self.pos]
        value = float(text) if "." in text else int(text)
        self.tokens.append(Token(NUMBER, value, line, col))

    def read_string(self):
        line, col = self.line, self.column
        quote = self.advance()  # buka
        parts = []              # segmen string: teks atau ekspresi
        chars = []              # buffer teks biasa
        has_interp = False
        while True:
            if self.pos >= len(self.source):
                raise SyntaxErrorTea("string tidak ditutup", line, col)
            ch = self.peek()
            if ch == quote:
                self.advance()  # tutup
                break
            if ch == "\\":
                self.advance()  # konsumsi backslash
                esc_line, esc_col = self.line, self.column
                esc = self.advance()
                if esc not in ESCAPES:
                    raise SyntaxErrorTea(
                        f"escape sequence tidak dikenal: \\{esc}",
                        esc_line, esc_col,
                    )
                chars.append(ESCAPES[esc])
                continue
            if ch == "$" and self.peek(1) == "{":
                # Interpolasi "${expr}"
                has_interp = True
                if chars:
                    parts.append(("text", "".join(chars)))
                    chars = []
                self.advance()  # $
                self.advance()  # {
                parts.append(self.read_interpolation(line))
                continue
            if ch == "\n":
                raise SyntaxErrorTea(
                    "string tidak boleh berisi newline; gunakan \\n",
                    self.line, self.column,
                )
            chars.append(self.advance())

        if not has_interp:
            self.tokens.append(Token(STRING, "".join(chars), line, col))
            return
        if chars:
            parts.append(("text", "".join(chars)))
        self.tokens.append(Token(INTERP, parts, line, col))

    def read_interpolation(self, string_line):
        """Baca isi ${...} sampai kurung tutup yang sepadan.

        Mengembalikan tuple ("expr", source, line, col) yang nantinya
        di-parse ulang oleh parser.
        """
        start_line = self.line
        start_col = self.column  # kolom karakter pertama ekspresi
        start = self.pos
        depth = 1
        while True:
            if self.pos >= len(self.source):
                raise SyntaxErrorTea(
                    "ekspresi ${...} tidak ditutup", string_line, start_col,
                )
            ch = self.peek()
            if ch == "{":
                depth += 1
                self.advance()
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
                self.advance()
            elif ch in "\"'":
                self.skip_string_literal(ch)
            elif ch == "\n":
                raise SyntaxErrorTea(
                    "ekspresi ${...} tidak boleh pindah baris",
                    self.line, self.column,
                )
            else:
                self.advance()
        source = self.source[start:self.pos]
        self.advance()  # konsumsi '}' penutup
        if not source.strip():
            raise SyntaxErrorTea("ekspresi kosong di dalam ${}",
                                 string_line, start_col)
        return ("expr", source, start_line, start_col)

    def skip_string_literal(self, quote):
        """Lewati string literal di dalam ekspresi ${...} (tanpa evaluasi)."""
        self.advance()  # buka
        while True:
            if self.pos >= len(self.source):
                raise SyntaxErrorTea("string tidak ditutup",
                                     self.line, self.column)
            ch = self.peek()
            if ch == "\\":
                self.advance()
                if self.pos < len(self.source):
                    self.advance()
                continue
            if ch == quote:
                self.advance()  # tutup
                return
            if ch == "\n":
                raise SyntaxErrorTea(
                    "string tidak boleh berisi newline; gunakan \\n",
                    self.line, self.column,
                )
            self.advance()

    def read_ident(self):
        line, col = self.line, self.column
        start = self.pos
        while True:
            c = self.peek()
            if c == "_" or c.isascii() and c.isalnum():
                self.advance()
            else:
                break
        text = self.source[start:self.pos]
        # Karakter setelahnya yang "mirip huruf" tapi bukan ASCII = salah ketik
        nxt = self.peek()
        if nxt and not nxt.isascii() and (nxt.isalpha() or nxt.isalnum()):
            self.error(self._pesan_karakter_aneh(nxt))
        if text in KEYWORDS:
            self.tokens.append(Token(KEYWORD, text, line, col))
        else:
            self.tokens.append(Token(IDENT, text, line, col))