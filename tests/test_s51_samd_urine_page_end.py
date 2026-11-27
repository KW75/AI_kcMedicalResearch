"""Session 51: the SaMD urine section also ends at a page break.

cli.py joins the pages of one file with a line '--- page N (kind) ---' and
parse_results reads the joined text. Before this change a URINALYSIS section
with no 'Released By' ran on into the next page for up to 60 lines, naming
those rows '- Urine'. The tests compare with the same lines read alone, so
they do not depend on the row field names.
"""
from pipelines.samd import report

U1 = 'Glucose 5.2 mmol/L 3.9-6.1'
B1 = 'Sodium 140 mmol/L 135-145'
B2 = 'Potassium 4.1 mmol/L 3.5-5.1'
NAME = "sample.pdf"
KIND = "lab report"


def rows(text):
    return report.parse_results([(NAME, KIND, text)])


def test_page_break_ends_urine_section():
    joined = rows("--- page 1 (lab report) ---\nURINALYSIS\n" + U1 + "\n\n"
                  "--- page 2 (lab report) ---\n" + B1 + "\n" + B2)
    alone = rows(B1 + "\n" + B2)
    assert len(alone) == 2
    assert joined[-2:] == alone


def test_urine_rows_before_break_still_marked():
    joined = rows("--- page 1 (lab report) ---\nURINALYSIS\n" + U1 + "\n\n"
                  "--- page 2 (lab report) ---\n" + B1)
    in_section = rows("URINALYSIS\n" + U1 + "\nReleased By: lab")
    plain = rows(U1)
    assert joined[0] == in_section[0]
    assert in_section[0] != plain[0]


def test_released_by_end_unchanged():
    got = rows("URINALYSIS\n" + U1 + "\nReleased By: lab\n" + B1)
    assert got[-1] == rows(B1)[0]
    assert got[0] != rows(U1)[0]


def test_urinalysis_on_page_two_starts_section():
    got = rows("--- page 1 (lab report) ---\n" + B1 + "\n\n"
               "--- page 2 (lab report) ---\nURINALYSIS\n" + U1)
    assert got[0] == rows(B1)[0]
    assert got[-1] == rows("URINALYSIS\n" + U1)[-1]
    assert got[-1] != rows(U1)[0]


def test_sixty_line_guard_kept():
    assert report._URINE_MAX == 60
