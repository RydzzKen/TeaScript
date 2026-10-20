#!/usr/bin/env python3
"""CLI TeaScript: `tea file.tea` atau `tea` untuk REPL.

Wrapper tipis — logika ada di teascript/cli.py.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from teascript.cli import main

if __name__ == "__main__":
    sys.exit(main())
