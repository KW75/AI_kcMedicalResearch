"""Session 48: menu 4 no longer names DuckDuckGo; Output line names both files.

Topic Search moved from DuckDuckGo to Europe PMC, but the [LOCAL AI]
notice, the cloud prompt, the menu text and search.py still named it.
The "Output :" line named only the .md although the .docx is written.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / "SOURCE_CODE" / "pipelines" / "search" / "search.py"
MAIN = ROOT / "SOURCE_CODE" / "main.py"


def _src(p):
    return p.read_text(encoding="utf-8")


def test_no_duckduckgo_in_search_or_main():
    for p in (SEARCH, MAIN):
        assert "duckduckgo" not in _src(p).lower(), p.name


def test_no_unused_ddg_constants():
    assert not re.search(r"\bDDG_", _src(SEARCH))


def test_search_services_are_pubmed_and_europe_pmc():
    assert re.search(r'"search":\s*\["PubMed", "Europe PMC"\],', _src(MAIN))


def test_menu_text_names_europe_pmc():
    src = _src(MAIN)
    assert "web synopsis" not in src
    assert "1. Topic Search  (Europe PMC synopsis with reference links)" in src


def test_found_line_says_records_not_web_results():
    src = _src(SEARCH)
    assert "web results" not in src
    assert "Europe PMC record(s)." in src


def test_output_line_names_md_and_docx():
    src = _src(SEARCH)
    assert src.count('print(f"  Output : output/search/{md_path.name}")') == 2
    assert src.count("if docx_path.exists():") == 2
    assert src.count('output/search/{docx_path.name}")') == 2
    assert '_{ts}.md")' not in src
