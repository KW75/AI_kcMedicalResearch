"""Session 45 (item d): 'Provider ... / model ...' was printed twice on the
console. Keep the first line (before the early exits, console only) and make
the run.log copy a 'Settings:' line so it no longer reads as a duplicate."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "sr" / "main.py"
OLD = 'logger.info(f"Provider {args.provider} / model {args.model}")'
NEW = 'logger.info(f"Settings: provider {args.provider} / model {args.model} (also shown above)")'


def _src():
    return SRC.read_text(encoding="utf-8")


def test_console_line_once():
    assert _src().count(OLD) == 1


def test_console_line_before_early_exits():
    s = _src()
    assert s.index(OLD) < s.index("sr_vision_error(args.model)") < s.index("attach_run_log(layout.project)")


def test_settings_line_in_run_log():
    s = _src()
    assert s.count(NEW) == 1
    assert s.index("attach_run_log(layout.project)") < s.index(NEW)
