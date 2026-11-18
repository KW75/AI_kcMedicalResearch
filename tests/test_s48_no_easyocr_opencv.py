"""Session 48: easyocr and opencv are no longer listed or imported.

No code imports easyocr or cv2 since utils/document_reader.py was removed
(PR #32). easyocr pulled in PyTorch (~2 GB), so both were dropped from
requirements-ocr.txt.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DROPPED = {
    "easyocr",
    "opencv-python",
    "opencv-python-headless",
    "opencv-contrib-python",
    "torch",
}


def _req_files():
    files = sorted(ROOT.glob("requirements*.txt"))
    files.append(ROOT / "SOURCE_CODE" / "pipelines" / "sr" / "requirements.txt")
    return files


def _names(path):
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line)
        if m:
            names.add(m.group(0).lower().replace("_", "-"))
    return names


def test_easyocr_and_opencv_not_listed():
    files = _req_files()
    assert len(files) >= 6
    listed = {f.name: sorted(_names(f) & DROPPED) for f in files}
    assert {k: v for k, v in listed.items() if v} == {}


def test_requirements_comments_do_not_mention_them():
    pat = re.compile(r"(?i)easyocr|opencv|pytorch")
    hits = [
        f"{f.name}:{i}"
        for f in _req_files()
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
        if pat.search(line)
    ]
    assert hits == []


def test_no_code_imports_easyocr_or_cv2():
    bad = []
    for folder in ("SOURCE_CODE", "scripts", "tests"):
        for py in (ROOT / folder).rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                else:
                    continue
                if any(m.split(".")[0] in {"easyocr", "cv2"} for m in mods):
                    bad.append(f"{py.relative_to(ROOT)}:{node.lineno}")
    assert bad == []
