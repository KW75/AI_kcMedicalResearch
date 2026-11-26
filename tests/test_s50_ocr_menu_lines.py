"""Session 50: OCR menu 8 with several files - a blank line between the file
list and "Write them as", and the Finance choice on one line (user request)."""
from pipelines.ocr import cli


def test_blank_line_before_the_choices():
    logs = []
    cli._ask_kind(lambda prompt="": "2", logs.append)
    assert logs[0] == "" and logs[1] == "Write them as"


def test_finance_choice_fits_one_line():
    fin = [line for line in cli.KIND_MENU if line.startswith("3. Finance")]
    assert len(fin) == 1
    assert fin[0] == ("3. Finance  - all invoices sum up to one table with "
                      "subtotals + total (CSV/HTML/DOCX/PDF)")
    assert "\n" not in fin[0]
