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


class NameErrorTea(TeaError):
    """Variabel belum dideklarasikan."""


class RuntimeErrorTea(TeaError):
    """Pembagian nol, tipe tidak cocok, dll."""