"""Author labels use the surname only (item 22, F13 c, Session 43).

Run 20261116_080329 mixed "Dennis C. Ang", "B. Karlsson" and "Jensen".
_mirror_study_metadata now shortens the final first_author to a surname and
keeps the full name in study_metadata["first_author_full"].
"""
from __future__ import annotations

from pipelines.sr.src.extraction import study_overrides as so_mod
from pipelines.sr.src.extraction.data_extractor import DataExtractor


def _mirror(author, year=2010):
    ex = DataExtractor.__new__(DataExtractor)
    r = {"filename": "x.pdf", "first_author": author, "year": year,
         "study_metadata": {"first_author": author, "year": year}}
    ex._mirror_study_metadata(r)
    return r


def test_full_name_becomes_surname_and_full_kept():
    r = _mirror("Dennis C. Ang")
    assert r["study_metadata"]["first_author"] == "Ang"
    assert r["study_metadata"]["first_author_full"] == "Dennis C. Ang"


def test_initial_then_surname():
    assert _mirror("B. Karlsson")["study_metadata"]["first_author"] == "Karlsson"


def test_top_level_follows():
    assert _mirror("Karin B. Jensen")["first_author"] == "Jensen"


def test_surname_only_unchanged():
    r = _mirror("Jensen")
    assert r["study_metadata"]["first_author"] == "Jensen"
    assert "first_author_full" not in r["study_metadata"]


def test_unparseable_left_as_is():
    r = _mirror("Ang 2010")
    assert r["study_metadata"]["first_author"] == "Ang 2010"
    assert "first_author_full" not in r["study_metadata"]


def test_given_first_particles_kept():
    assert so_mod._first_author_from_string("Anna van der Berg") == "van der Berg"


def test_surname_first_particles_still_work():
    assert so_mod._first_author_from_string("van der Berg, Anna") == "van der Berg"


def test_short_given_name_not_taken_as_particle():
    assert so_mod._first_author_from_string("Le Wang") == "Wang"
