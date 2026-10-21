"""Tiga jenis error TeaScript: sintaks, nama, runtime."""


class TeaError(Exception):
    """Base error dengan nomor baris dan kolom."""

    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format())

    def format(self):
        if self.line is not None and self.column is not None:
            return f"Error (baris {self.line}, kolom {self.column}): {self.message}"
        if self.line is not None:
            return f"Error (baris {self.line}): {self.message}"
        return f"Error: {self.message}"


class SyntaxErrorTea(TeaError):
    """Error saat parsing."""

    kind = "sintaks"


class NameErrorTea(TeaError):
    """Variabel belum dideklarasikan."""

    kind = "nama"


class RuntimeErrorTea(TeaError):
    """Pembagian nol, tipe tidak cocok, dll."""

    kind = "runtime"


class CaughtError:
    """Error yang sudah ditangkap blok `catch`.

    Nilai inilah yang diikat ke variabel di `catch e { ... }`.

    Field:
      message         : pesan error polos (tanpa posisi)
      line, column    : posisi error di kode (bisa None)
      kind            : jenis error — "sintaks", "nama", "runtime", "python"
      cause           : exception Python asli, kalau error berasal dari
                        pemanggilan fungsi Python (pyimport)
    """

    def __init__(self, message, line=None, column=None, kind="runtime",
                 cause=None):
        self.message = message
        self.line = line
        self.column = column
        self.kind = kind
        self.cause = cause

    @classmethod
    def from_error(cls, err):
        """Buat dari TeaError (error yang dibuat interpreter sendiri)."""
        cause = getattr(err, "cause", None)
        kind = getattr(err, "kind", "runtime")
        if cause is not None:
            # error asalnya dari fungsi Python (pyimport)
            kind = "python"
        return cls(err.message,
                   line=err.line,
                   column=getattr(err, "column", None),
                   kind=kind,
                   cause=cause)

    @classmethod
    def from_python(cls, err, line=None):
        """Buat dari exception Python mentah (mis. dari pyimport)."""
        pesan = f"{type(err).__name__}: {err}"
        return cls(pesan, line=line, kind="python", cause=err)

    @property
    def text(self):
        """Teks lengkap: pesan + posisi, sama seperti error yang tidak ditangkap."""
        if self.line is not None and self.column is not None:
            return f"Error (baris {self.line}, kolom {self.column}): {self.message}"
        if self.line is not None:
            return f"Error (baris {self.line}): {self.message}"
        return f"Error: {self.message}"

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"<error {self.kind}: {self.message}>"