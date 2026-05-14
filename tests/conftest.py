"""Pytest config: make plugin root importable so tests can import adapter.py.

The plugin's main.py does this at runtime via sys.path.insert; tests need
the same.
"""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
