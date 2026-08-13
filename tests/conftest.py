"""
Pytest configuration and shared fixtures.
"""
import sys
from pathlib import Path

# CI fix: override sqlite3 with pysqlite3-binary for chromadb compatibility
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass  # Not on CI/Linux - native sqlite3 is fine

# Ensure SOURCE_CODE is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
