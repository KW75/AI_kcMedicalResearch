"""[PLAUSIBILITY] message prints the absolute effect size (F13 b).

Run 20261116_080329 printed |SMD|=-8.575: _check_plausibility tested
abs(est) against the bound but printed the signed est in the message.
"""
from __future__ import annotations

from SOURCE_CODE.pipelines.sr.main import _check_plausibility


def test_negative_smd_prints_absolute_value():
    msg = _check_plausibility("SMD", -8.575, "Lami (2017)")
    assert msg is not None
    assert "|SMD|=8.575" in msg
    assert "-8.575" not in msg


def test_positive_smd_unchanged():
    msg = _check_plausibility("SMD", 2.1, "X")
    assert msg is not None
    assert "|SMD|=2.100" in msg


def test_negative_smd_inside_bound_not_flagged():
    assert _check_plausibility("SMD", -1.2, "X") is None


def test_or_unchanged():
    msg = _check_plausibility("OR", 15.0, "X")
    assert msg is not None
    assert "|OR|=15.000" in msg