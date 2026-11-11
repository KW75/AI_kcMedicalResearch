"""Write prisma_criteria.yaml only when its content changes.

Session 37: the launcher rebuilt the file on every run with PyYAML's default
80-character width, which wrapped the long comparator line and left the git
tree modified after every run even though the meaning was unchanged.
"""
from pathlib import Path

import yaml

_NO_WRAP = 10 ** 6   # effectively never wrap long values


def _dump(cfg: dict) -> str:
    return yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False,
                          width=_NO_WRAP)


def _read_existing(path: Path):
    """Parsed content of the existing file, or None if missing/unreadable."""
    try:
        return yaml.safe_load(path.read_bytes().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None


def write_criteria_if_changed(path, cfg: dict) -> bool:
    """Write cfg to path unless the file already holds the same content.

    Compares parsed YAML, so line wrapping, CRLF and a BOM in the existing
    file don't count as changes. Returns True if the file was written.
    """
    path = Path(path)
    if path.exists() and _read_existing(path) == cfg:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_dump(cfg).encode("utf-8"))   # UTF-8, no BOM
    return True

def placeholder_fields(cfg):
    """Session 38 (7h): fields still holding a <...> placeholder from the sample config."""
    def _ph(v):
        return isinstance(v, str) and v.strip().startswith("<") and v.strip().endswith(">")
    if not isinstance(cfg, dict):
        return []
    found = [k for k in ("review_title", "effect_measure") if _ph(cfg.get(k))]
    pico = cfg.get("pico") if isinstance(cfg.get("pico"), dict) else {}
    found += [f"pico.{k}" for k in ("population", "intervention", "comparator", "outcome")
              if _ph(pico.get(k))]
    return found
