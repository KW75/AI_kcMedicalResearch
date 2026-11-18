"""Session 48: appraisal on local AI must not overflow Ollama's context.

Ollama keeps num_ctx (default 32768 tokens) for prompt + answer and
silently drops the START of a prompt that is too long - for appraisal
that is the guidelines. Menu 3 sends each whole article, so a local run
now skips an article above APPRAISAL_LOCAL_MAX_CHARS (same budget as
writing.SYNOPSIS_LOCAL_MAX_CHARS) and appraises the rest. Cloud runs and
callers that do not pass local= are unchanged.

Also: the prompt's word limit was lost to encoding ("<= 200" -> "??200"
-> " - 200", commits b82f4d2 / 9aef3e6); it now says "at most 200 words".
"""
from pathlib import Path
from unittest.mock import patch

import pipelines.appraisal.appraisal as ap

LIMIT = 80_000
LONG = "L" * (LIMIT + 1)
SHORT = "Short CBT article about pain."


def _run(tmp_path, files, **kw):
    dirs = {k: tmp_path / k for k in ("docs", "input", "output", "reports")}
    for d in dirs.values():
        d.mkdir()
    for name, text in files.items():
        (dirs["input"] / name).write_text(text, encoding="utf-8")
    prompts = []

    def fake_llm(system_prompt, user_prompt):
        prompts.append(user_prompt)
        return "Mock appraisal"

    with patch("pipelines.appraisal.appraisal._paths") as mp:
        mp.return_value = {
            "doc_root": dirs["docs"],
            "input": dirs["input"],
            "output": dirs["output"],
            "reports": dirs["reports"],
        }
        ap.run_appraisal(direct_instructions=[], call_llm_fn=fake_llm,
                         verbose=False, **kw)
    return prompts, dirs


def test_limit_matches_writing_budget():
    assert ap.APPRAISAL_LOCAL_MAX_CHARS == LIMIT


def test_local_skips_long_article_and_appraises_the_rest(tmp_path, capsys):
    prompts, dirs = _run(tmp_path, {"long.txt": LONG, "short.txt": SHORT},
                         local=True)
    assert len(prompts) == 1
    assert SHORT in prompts[0]
    assert not any("L" * 50 in p for p in prompts)
    out = capsys.readouterr().out
    assert "long.txt" in out and "too large for local AI" in out
    names = [f.name for f in dirs["output"].glob("*.md")]
    assert names and not any("long" in n for n in names)


def test_local_article_at_limit_is_sent(tmp_path):
    prompts, _ = _run(tmp_path, {"edge.txt": "E" * LIMIT}, local=True)
    assert len(prompts) == 1


def test_cloud_sends_long_article(tmp_path):
    prompts, _ = _run(tmp_path, {"long.txt": LONG, "short.txt": SHORT},
                      local=False)
    assert len(prompts) == 2


def test_default_is_not_local(tmp_path):
    prompts, _ = _run(tmp_path, {"long.txt": LONG})
    assert len(prompts) == 1


def test_done_line_counts_skipped(tmp_path, capsys):
    _run(tmp_path, {"long.txt": LONG, "short.txt": SHORT}, local=True)
    out = capsys.readouterr().out
    assert "1 article(s) processed" in out
    assert "1 skipped" in out


def test_prompt_word_limit_is_readable():
    p = ap._appraiser_user_prompt([], "text", "stem")
    assert "at most 200 words" in p
    assert " - 200 words" not in p


def test_menu3_passes_local_flag():
    src = (Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "main.py"
           ).read_text(encoding="utf-8")
    start = src.index("def handle_appraisal_mode(")
    body = src[start:src.index("\ndef ", start + 1)]
    assert 'local=(provider == "ollama")' in body
