"""Session 37: one shared text per paper for SR screening, RoB2 and extraction.

get_paper_text(pdf_path, cache_dir, read_pages=..., ocr_png=...) returns a dict:
  text            - pages joined with '--- page N ---' markers
  unknown         - number of [?] left in text
  scanned_pages   - pages read by Tesseract (no text layer)
  unreadable_pages- scanned pages Tesseract could not read (missing/failed)
  from_cache      - True if the saved file was reused
  path            - the saved <cache_dir>/<pdf stem>.txt

Page dicts follow pipelines/ocr/reader.py: text-layer page {"text": ...};
broken-symbol page {"png": ..., "hint": text with [?]}; scanned page
{"png": ...} only. The saved file is what a doctor edits to fix [?]; a rerun
must use it, not re-read the PDF.
"""
import importlib

import pytest

CLEAN = {"page": 1, "text": "Randomised controlled trial of CBT.", "png": None}
BROKEN = {"page": 2, "text": None, "png": b"png2",
          "hint": "Pain 4.4 [?] 13.7 (n [?] 32)"}
SCAN = {"page": 3, "text": None, "png": b"png3"}


@pytest.fixture(scope="module")
def pt():
    mod = None
    for name in ("pipelines.sr.src.utils.paper_text",
                 "SOURCE_CODE.pipelines.sr.src.utils.paper_text"):
        try:
            mod = importlib.import_module(name)
            break
        except ModuleNotFoundError:
            pass
    assert mod is not None, "pipelines/sr/src/utils/paper_text.py missing (shared paper text)"
    return mod


def _reader(*pages):
    return lambda _path: [dict(p) for p in pages]


def _no_ocr(_png):
    pytest.fail("Tesseract must not be called for pages with a text layer")


def test_clean_text_layer(pt, tmp_path):
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(CLEAN), ocr_png=_no_ocr)
    assert "Randomised controlled trial of CBT." in r["text"]
    assert r["unknown"] == 0
    assert r["scanned_pages"] == []
    assert r["from_cache"] is False


def test_broken_symbols_kept_as_marks_and_counted(pt, tmp_path):
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(BROKEN), ocr_png=_no_ocr)
    assert "Pain 4.4 [?] 13.7 (n [?] 32)" in r["text"]
    assert r["unknown"] == 2


def test_scanned_page_read_by_tesseract(pt, tmp_path):
    calls = []
    def ocr(png):
        calls.append(png)
        return "Scanned page text"
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(SCAN), ocr_png=ocr)
    assert "Scanned page text" in r["text"]
    assert calls == [b"png3"]
    assert r["scanned_pages"] == [3]
    assert r["unreadable_pages"] == []


def test_scanned_page_without_tesseract_is_marked_not_crashed(pt, tmp_path, caplog):
    def ocr(_png):
        raise RuntimeError("tesseract is not installed or not in PATH")
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(CLEAN, SCAN), ocr_png=ocr)
    assert "[page 3: no text layer" in r["text"]
    assert r["unreadable_pages"] == [3]
    assert "Tesseract" in caplog.text


def test_pages_in_order_with_markers(pt, tmp_path):
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(CLEAN, BROKEN, SCAN),
                          ocr_png=lambda _png: "scan")
    t = r["text"]
    assert t.index("--- page 1 ---") < t.index("--- page 2 ---") < t.index("--- page 3 ---")


def test_writes_cache_file_without_bom(pt, tmp_path):
    r = pt.get_paper_text("dir/a.pdf", tmp_path, read_pages=_reader(CLEAN), ocr_png=_no_ocr)
    saved = tmp_path / "a.txt"
    assert saved.exists()
    assert str(r["path"]) == str(saved)
    raw = saved.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert "Randomised controlled trial" in raw.decode("utf-8")


def test_second_call_reuses_file_without_rereading(pt, tmp_path):
    pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(BROKEN), ocr_png=_no_ocr)
    def must_not_read(_path):
        pytest.fail("rerun must use the saved text, not re-read the PDF")
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=must_not_read, ocr_png=_no_ocr)
    assert r["from_cache"] is True
    assert r["unknown"] == 2


def test_manual_correction_is_respected(pt, tmp_path):
    pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(BROKEN), ocr_png=_no_ocr)
    saved = tmp_path / "a.txt"
    fixed = saved.read_text(encoding="utf-8").replace("4.4 [?] 13.7", "4.4 \u00b1 13.7") \
                                               .replace("(n [?] 32)", "(n = 32)")
    saved.write_bytes(fixed.encode("utf-8"))
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(BROKEN), ocr_png=_no_ocr)
    assert "4.4 \u00b1 13.7" in r["text"]
    assert "(n = 32)" in r["text"]
    assert r["unknown"] == 0

# --- broken-font pages (Session 37: Karlsson 2015, McCrae 2019) -------------
# Every page of these two papers has ~10-14% broken characters (the font
# shifted letters and spaces); Ang/Jensen/Lami stay <= 1.3%. A page with
# ratio >= 0.05 AND >= 20 [?] goes to Tesseract instead of the [?] route.

FONT_HINT = "[?]".join(["P]in"] * 30)            # 29 [?], ratio ~0.19
FONT = {"page": 4, "text": None, "png": b"png4", "hint": FONT_HINT}
LONG_HINT = "Methods " * 300 + " ".join(["(n [?] 32)"] * 25)   # 25 [?], ratio ~0.01
LONG = {"page": 5, "text": None, "png": b"png5", "hint": LONG_HINT}


def test_broken_font_page_read_by_tesseract(pt, tmp_path):
    calls = []
    def ocr(png):
        calls.append(png)
        return "Scandinavian Journal of Pain 9 (2015) 11-21"
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(CLEAN, FONT), ocr_png=ocr)
    assert calls == [b"png4"]
    assert "Scandinavian Journal of Pain 9 (2015) 11-21" in r["text"]
    assert "--- page 4 --- (Tesseract, broken font)" in r["text"]
    assert r["unknown"] == 0
    assert r["broken_font_pages"] == [4]
    assert r["scanned_pages"] == []


def test_broken_font_page_without_tesseract_keeps_marks(pt, tmp_path, caplog):
    def ocr(_png):
        raise RuntimeError("tesseract is not installed or not in PATH")
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(FONT), ocr_png=ocr)
    assert FONT_HINT in r["text"]
    assert r["unknown"] == 29
    assert r["broken_font_pages"] == []
    assert "Tesseract" in caplog.text


def test_many_marks_in_long_text_stay_on_mark_route(pt, tmp_path):
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(LONG), ocr_png=_no_ocr)
    assert r["unknown"] == 25


def test_rerun_from_cache_reports_broken_font_pages(pt, tmp_path):
    pt.get_paper_text("a.pdf", tmp_path, read_pages=_reader(FONT),
                      ocr_png=lambda _png: "Readable text")
    def must_not_read(_path):
        pytest.fail("rerun must use the saved text, not re-read the PDF")
    r = pt.get_paper_text("a.pdf", tmp_path, read_pages=must_not_read, ocr_png=_no_ocr)
    assert r["from_cache"] is True
    assert r["broken_font_pages"] == [4]
    assert r["scanned_pages"] == []
