"""Definisi AST. Setiap node menyimpan nomor baris untuk error runtime."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    line: int = 0


# --- Expressions ---
@dataclass
class Number(Node):
    value: Any = None


@dataclass
class String(Node):
    value: str = ""


@dataclass
class Bool(Node):
    value: bool = False


@dataclass
class Nil(Node):
    pass


@dataclass
class Ident(Node):
    name: str = ""


@dataclass
class Binary(Node):
    op: str = ""
    left: Node = None
    right: Node = None


@dataclass
class Unary(Node):
    op: str = ""
    operand: Node = None


@dataclass
class Call(Node):
    callee: Node = None
    args: list = field(default_factory=list)


@dataclass
class Index(Node):
    target: Node = None
    index: Node = None


@dataclass
class Slice(Node):
    target: Node = None
    start: Node = None  # boleh None → dari awal
    end: Node = None    # boleh None → sampai akhir


@dataclass
class Ternary(Node):
    condition: Node = None
    then: Node = None
    otherwise: Node = None


@dataclass
class Interp(Node):
    # campuran str (teks biasa) dan Node (ekspresi ${...})
    parts: list = field(default_factory=list)


@dataclass
class ListLit(Node):
    elements: list = field(default_factory=list)


@dataclass
class DictLit(Node):
    pairs: list = field(default_factory=list)  # list (key_node, value_node)


# --- Statements ---
@dataclass
class Let(Node):
    name: str = ""
    value: Node = None


@dataclass
class KwArg(Node):
    # Keyword argument untuk fungsi Python di dalam daftar argumen.
    # Ditulis `let _nama = nilai`; pasangan nama/nilai berlaku untuk
    # pemanggilan yang memuat KwArg.
    name: str = ""
    value: Node = None


@dataclass
class Bind(Node):
    # `let nama = nilai` di dalam daftar argumen: nilai dihitung di lingkup
    # sekarang, ekspresi balikannya adalah nilai itu (mis. print(let x = 1)).
    name: str = ""
    value: Node = None


@dataclass
class Assign(Node):
    name: str = ""
    value: Node = None


@dataclass
class IndexAssign(Node):
    target: Node = None
    index: Node = None
    value: Node = None


@dataclass
class If(Node):
    condition: Node = None
    then_body: list = field(default_factory=list)
    else_body: list = field(default_factory=list)


@dataclass
class While(Node):
    condition: Node = None
    body: list = field(default_factory=list)


@dataclass
class ForIn(Node):
    name: str = ""
    iterable: Node = None
    body: list = field(default_factory=list)


@dataclass
class Break(Node):
    pass


@dataclass
class Continue(Node):
    pass


@dataclass
class Import(Node):
    # path=None → cari "<nama>.tea"; path terisi → path eksplisit
    name: str = ""
    path: str = None


@dataclass
class FromImport(Node):
    module: str = ""
    names: list = field(default_factory=list)


@dataclass
class FnDef(Node):
    name: str = ""
    params: list = field(default_factory=list)
    body: list = field(default_factory=list)


@dataclass
class Return(Node):
    value: Node = None


@dataclass
class ExprStmt(Node):
    expr: Node = None


@dataclass
class Program(Node):
    statements: list = field(default_factory=list)