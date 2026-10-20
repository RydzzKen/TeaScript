#!/usr/bin/env python3
"""Jalankan playground web TeaScript: python3 webapp.py [--port 5000]"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from teascript.web import main

if __name__ == "__main__":
    sys.exit(main())
