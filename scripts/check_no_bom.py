"""Fail if any Python source file starts with a UTF-8 BOM.

Python tolerates a BOM on import, but ast.parse() rejects it, and combined
with an encoding mismatch it renders as garbage characters in editors -
which is how 23 files in this repo came to look like corrupted comments.

PowerShell 5 `Set-Content -Encoding UTF8` writes a BOM. Use
`-Encoding utf8NoBOM` (PS7) or [System.IO.File]::WriteAllText with
UTF8Encoding($false).
"""
import glob
import sys

bad = []
for path in glob.glob("SOURCE_CODE/**/*.py", recursive=True):
    with open(path, "rb") as handle:
        if handle.read(3) == b"\xef\xbb\xbf":
            bad.append(path)

if bad:
    print("UTF-8 BOM found in %d file(s):" % len(bad))
    for path in bad:
        print("   ", path)
    print("\nStrip with scripts/strip_bom.py")
    sys.exit(1)

print("No BOMs found.")
