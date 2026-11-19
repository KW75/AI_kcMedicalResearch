"""Session 48: an HTTP error from Europe PMC prints an error line.

Before, a non-200 answer (for example 500 or 503) returned [] with no
message, so menu 4 showed only "No results found" although the server
had failed.
"""
from unittest.mock import MagicMock, patch

import pytest

from pipelines.search import search as s


def _resp(status, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload or {"resultList": {"result": []}}
    return r


@pytest.mark.parametrize("status", [429, 500, 503])
def test_http_error_prints_error_line(status, capsys):
    with patch.object(s.requests, "get", return_value=_resp(status)):
        result = s._europepmc_search("asthma")
    out = capsys.readouterr().out
    assert result == []
    assert f"[SEARCH] Europe PMC error: HTTP {status}" in out
    assert "Try again later." in out


def test_ok_with_no_records_prints_no_error(capsys):
    with patch.object(s.requests, "get", return_value=_resp(200)):
        result = s._europepmc_search("asthma")
    assert result == []
    assert "error" not in capsys.readouterr().out.lower()
