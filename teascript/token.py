"""Definisi token. Nomor baris & kolom disimpan sejak lexer."""

from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: object
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"


# Tipe token
NUMBER = "NUMBER"
STRING = "STRING"
INTERP = "INTERP"  # string dengan interpolation "${expr}"
IDENT = "IDENT"
KEYWORD = "KEYWORD"
OP = "OP"
PUNCT = "PUNCT"
EOF = "EOF"

KEYWORDS = {
    "let", "if", "else", "while", "fn", "return",
    "true", "false", "nil", "and", "or", "not",
    "for", "in", "break", "continue",
    "import", "from",
    "try", "catch",
}

# Operator dua karakter lebih dulu
TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "+=", "-=", "*=", "/=", "%="}
ONE_CHAR_OPS = set("+-*/%<>=?")
PUNCTUATION = set("(){}[],:.")

# Operator assignment gabungan (untuk parser)
COMPOUND_OPS = {"+=", "-=", "*=", "/=", "%="}