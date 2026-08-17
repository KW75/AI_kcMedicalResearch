"""Strip UTF-8 BOMs from Python source files under SOURCE_CODE/.

Run after scripts/check_no_bom.py reports failures.
"""
import glob

stripped = []
for path in glob.glob("SOURCE_CODE/**/*.py", recursive=True):
    with open(path, "rb") as handle:
        data = handle.read()
    if data.startswith(b"\xef\xbb\xbf"):
        with open(path, "wb") as handle:
            handle.write(data[3:])
        stripped.append(path)

if stripped:
    print("Stripped BOM from %d file(s):" % len(stripped))
    for path in stripped:
        print("   ", path)
else:
    print("No BOMs found; nothing to do.")
