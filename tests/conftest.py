"""
Pytest configuration and shared fixtures.
"""
import sys
from pathlib import Path

# Ensure SOURCE_CODE is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
