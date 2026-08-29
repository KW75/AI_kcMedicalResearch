#!/usr/bin/env python
# SOURCE_CODE/pipelines/sr/scripts/nondet_probe.py
"""Measure extraction non-determinism (#11) on a set of PDFs.

Runs DataExtractor.extract_by_pdf_path N times per PDF and reports, per
field, whether all runs agreed. This is the machine version of the manual
"run 3x and diff" reviewer step, and the yardstick for judging whether a
sampling change (temperature/seed) or an N=3 agreement flag helped.

Usage (from SOURCE_CODE/pipelines/sr, with .env loaded or DASHSCOPE/QWEN
key in the environment):

    python ../../scripts/nondet_probe.py --runs 3 \
        input/ang.pdf input/jensen.pdf input/lami.pdf

Exercise the production N=3 flag (each "run" is itself 3 voted calls):

    python scripts/nondet_probe.py --runs 2 --agreement 3 ...

A/B the pre-S26 behaviour (vision at 0.1, no seed) against t=0/seed=42:

    SR_EXTRACT_TEMPERATURE=0.1 SR_EXTRACT_SEED=none python ../../scripts/nondet_probe.py --runs 3 --tag baseline ...
    python ../../scripts/nondet_probe.py --runs 3 --tag t0seed42 ...

Outputs: prints a per-PDF agreement table, writes
<out>/nondet_<tag>_<timestamp>.json with every raw result. Exit code 1 if
any tracked field disagreed across runs, so it can gate a script.

Nothing here is verified against source quotes. Three runs that agree on
a wrong number still agree; this tool measures stability, not correctness.
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Locate the SR package regardless of where the script is invoked from.
# ---------------------------------------------------------------------------
def _import_extractor():
    here = Path(__file__).resolve()
    candidates = [
        Path.cwd(),
        here.parents[1],                                            # sr/scripts or sr/src
        here.parents[1] / "SOURCE_CODE" / "pipelines" / "sr",      # repo-root/scripts
        here.parents[1] / "pipelines" / "sr",                       # SOURCE_CODE/scripts
    ]
    for root in candidates:
        if (root / "src" / "extraction" / "data_extractor.py").exists():
            sys.path.insert(0, str(root))
            from src.extraction.data_extractor import DataExtractor  # noqa
            return DataExtractor, root
    sys.exit("Could not find src/extraction/data_extractor.py; run from "
             "SOURCE_CODE/pipelines/sr or fix the path list in _import_extractor().")


def _load_dotenv(path):
    """Tiny .env loader so python-dotenv isn't a hard dependency."""
    if not path or not Path(path).exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(path)
        return
    except ImportError:
        pass
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _load_pico(path):
    if not path:
        return {}
    try:
        import yaml
    except ImportError:
        sys.exit("pyyaml needed to read --pico; pip install pyyaml")
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    # Accept either a flat PICO dict or a top-level 'pico' key.
    return data.get("pico", data)


# ---------------------------------------------------------------------------
# Field selection: what the reviewer actually diffs.
# ---------------------------------------------------------------------------
TRACKED = [
    ("extraction_method", ("extraction_method",)),
    ("intervention_group", ("intervention_group",)),
    ("control_group", ("control_group",)),
    ("outcome_selected", ("primary_outcome", "outcome_selected")),
    ("timepoint_selected", ("primary_outcome", "timepoint_selected")),
    ("mean_i", ("primary_outcome", "mean_intervention")),
    ("sd_i", ("primary_outcome", "sd_intervention")),
    ("mean_c", ("primary_outcome", "mean_control")),
    ("sd_c", ("primary_outcome", "sd_control")),
    ("n_i", ("participants", "n_intervention")),
    ("n_c", ("participants", "n_control")),
    ("quote_i#", ("primary_outcome", "source_quote_intervention")),
    ("quote_c#", ("primary_outcome", "source_quote_control")),
    ("extraction_error", ("extraction_error",)),
    ("nondet_flag", ("nondet_flag",)),
]
HASHED = {"quote_i#", "quote_c#"}


def _dig(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _norm(label, v):
    if v is None:
        return None
    if label in HASHED:
        return hashlib.sha1(str(v).strip().encode()).hexdigest()[:8]
    if isinstance(v, float):
        return round(v, 6)
    return v


def _flatten(result):
    return {label: _norm(label, _dig(result, path)) for label, path in TRACKED}


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+", help="PDF paths")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--provider", default="qwen")
    ap.add_argument("--model", default="qwen-vl-plus")
    ap.add_argument("--pico", default=None,
                    help="prisma_criteria.yaml (or any yaml with a pico block)")
    ap.add_argument("--env", default=".env", help=".env to load (default ./.env)")
    ap.add_argument("--temperature", type=float, default=None,
                    help="override; else SR_EXTRACT_TEMPERATURE env, else 0")
    ap.add_argument("--seed", default=None,
                    help="override; int or 'none'; else SR_EXTRACT_SEED env, else 42")
    ap.add_argument("--agreement", type=int, default=1,
                    help="internal N-run agreement per extraction (default 1 = "
                         "measure raw variance; 3 = exercise the production flag)")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between calls")
    ap.add_argument("--tag", default="probe", help="label in output filename")
    ap.add_argument("--out", default="output/nondet", help="output dir")
    args = ap.parse_args()

    _load_dotenv(args.env)
    DataExtractor, root = _import_extractor()

    kw = {}
    if args.temperature is not None:
        kw["temperature"] = args.temperature
    if args.seed is not None:
        kw["seed"] = None if args.seed.lower() == "none" else int(args.seed)

    ex = DataExtractor(pico_criteria=_load_pico(args.pico),
                       provider=args.provider, model=args.model,
                       n_agreement=args.agreement, **kw)
    print(f"[probe] package root={root}")
    print(f"[probe] provider={ex.provider} model={ex.model} "
          f"temperature={ex.temperature} seed={ex.seed} runs={args.runs} "
          f"agreement={ex.n_agreement}")

    report = {
        "tag": args.tag,
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "provider": ex.provider, "model": ex.model,
        "temperature": ex.temperature, "seed": ex.seed, "runs": args.runs,
        "agreement": ex.n_agreement,
        "pdfs": {},
    }
    any_disagreement = False

    for pdf in args.pdfs:
        pdf = str(pdf)
        name = Path(pdf).name
        raws, flats = [], []
        for i in range(1, args.runs + 1):
            t0 = time.time()
            r = ex.extract_by_pdf_path(pdf, name)
            dt = time.time() - t0
            raws.append(r)
            flats.append(_flatten(r))
            print(f"[probe] {name} run {i}/{args.runs} done in {dt:.1f}s "
                  f"method={r.get('extraction_method')} err={r.get('extraction_error')}")
            if i < args.runs:
                time.sleep(args.delay)

        disagree = []
        print(f"\n=== {name} ===")
        w = max(len(l) for l, _ in TRACKED)
        hdr = f"{'field':<{w}} | " + " | ".join(f"run{i+1:<10}" for i in range(args.runs)) + " | agree"
        print(hdr)
        print("-" * len(hdr))
        for label, _ in TRACKED:
            vals = [f[label] for f in flats]
            ok = len({json.dumps(v, sort_keys=True) for v in vals}) == 1
            if not ok:
                disagree.append(label)
            cells = " | ".join(f"{str(v)[:11]:<11}" for v in vals)
            print(f"{label:<{w}} | {cells} | {'yes' if ok else 'NO'}")
        print(f"disagreeing fields: {disagree or 'none'}\n")
        any_disagreement |= bool(disagree)
        report["pdfs"][name] = {"disagree": disagree, "flat": flats, "raw": raws}

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"nondet_{args.tag}_{stamp}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    n_bad = sum(1 for v in report["pdfs"].values() if v["disagree"])
    print(f"[probe] {n_bad}/{len(report['pdfs'])} PDFs had disagreement; wrote {out}")
    sys.exit(1 if any_disagreement else 0)


if __name__ == "__main__":
    main()
