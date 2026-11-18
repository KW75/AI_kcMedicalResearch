"""Session 48: OCR Papers mode failed on the Ang PDF with [Errno 22].

Papers mode uses each file's full stem as header (cli._run_papers, f.stem);
output._record_stem then repeats the source stem in the record name:
header(121) + date + stem(121) + '_pdf.md' ~ 260 characters in ONE name.
NTFS (and ext4) refuse any single name over 255 even with long paths on.
All AI work (139 [?] filled) was lost at the final write. Fix: cap the
name part of the header and the source part of the record stem; a cut
source stem gets a short hash so two long names cannot clash. Short
names are unchanged. A failed save is no longer reported as 'Could not
read'.
"""
from datetime import datetime
from pathlib import Path

from pipelines.ocr import output

NOW = datetime(2026, 11, 18, 14, 30)
ANG = ("Arthritis Care Research - 2010 - Ang - Cognitive behavioral therapy "
       "attenuates nociceptive responding in patients with-1.pdf")
ANG_STEM = Path(ANG).stem


def test_long_header_is_capped_and_readable():
    h = output.make_header(ANG_STEM, NOW)
    assert h.startswith("Arthritis_Care_Research")
    assert h.endswith("_2026-11-18")
    assert len(h) <= 40 + len("_2026-11-18")


def test_short_header_unchanged():
    assert output.make_header("Cardio lectures", NOW) == "Cardio_lectures_2026-11-07".replace("07", "18")


def test_long_record_files_are_written_with_short_names(tmp_path):
    header = output.make_header(ANG_STEM, NOW)
    rec_dir = tmp_path / header
    pages = [{"page": 1, "text": "mean \u00b1 SD", "method": "hybrid"}]
    output.write_record(tmp_path, header, ANG, "Summary.", pages,
                        "qwen3-vl:30b-a3b-instruct", rec_dir=rec_dir)
    written = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert written, "no record written"
    for p in written:
        for part in p.relative_to(tmp_path).parts:
            assert len(part) <= 120, f"{len(part)} chars: {part}"


def test_two_long_names_do_not_clash():
    a = ANG.replace("with-1.pdf", "with-1.pdf")
    b = ANG.replace("with-1.pdf", "with-2.pdf")
    assert output._record_stem("H", a) != output._record_stem("H", b)


def test_short_record_stem_unchanged():
    assert output._record_stem("H", "IMG_1150.JPG") == "H_IMG_1150_jpg"


def test_failed_save_not_called_could_not_read():
    src = (Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines"
           / "ocr" / "cli.py").read_text(encoding="utf-8")
    assert "Could not read {name}" not in src
    assert "Not written: {name}" in src
