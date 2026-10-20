"""TeaScript — interpreter bahasa pemrograman kecil bergaya JavaScript/Python."""

try:
    from importlib.metadata import version as _version
    __version__ = _version("teascript")
except Exception:  # belum terpasang (dijalankan dari sumber)
    __version__ = "0.5.1"