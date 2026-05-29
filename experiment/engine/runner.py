"""Generic sweep runner.

Reads a sweep-config module (see `sweeps/sweep1_p0.py`), expands every cell ×
phrasing × repetition, calls the model, attaches both oracle comparisons, and
writes a full JSONL log plus a tidy CSV for analysis. Knows nothing about any
particular scenario or parameter — it only follows `cfg.SWEEP_VAR`.
"""

from __future__ import annotations

import importlib
import json
import random
from datetime import datetime
from types import ModuleType

import pandas as pd

from engine import oracle
from engine.config import RESULTS_DIR
from engine.params import Cell

# Columns kept in the tidy analysis CSV (full detail stays in the JSONL).
_CSV_COLUMNS = [
    "run_id", "sweep", "scenario", "model", "level", "phrasing_idx", "rep",
    "blameworthiness", "inferred_probability",
    "oracle_at_reference", "oracle_at_inferred", "error",
]


def _append_jsonl(path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(cfg: ModuleType, *, dry_run: bool = False, limit: int | None = None) -> str:
    """Execute the sweep described by `cfg`. Returns the parsed-CSV path."""
    scenario = importlib.import_module(f"prompts.{cfg.SCENARIO}.scenario")
    rng = random.Random(cfg.SEED)

    RESULTS_DIR.mkdir(exist_ok=True)
    # When launched via `python -m`, cfg.__name__ is "__main__"; use the filename.
    from pathlib import Path
    sweep_name = Path(getattr(cfg, "__file__", cfg.__name__)).stem
    model_slug = cfg.MODEL.split("/")[-1]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"{sweep_name}_{model_slug}_{stamp}"
    raw_path = RESULTS_DIR / f"raw_{tag}.jsonl"

    rows: list[dict] = []
    n_calls = 0

    for level in cfg.LEVELS:
        cell = Cell(**{**cfg.HELD, cfg.SWEEP_VAR: level})
        oracle_ref = oracle.oracle_blame(cell)
        n_phrasings = len(scenario.PHRASINGS[cfg.SWEEP_VAR][level])

        for phrasing_idx in range(n_phrasings):
            for rep in range(cfg.REPS):
                if limit is not None and n_calls >= limit:
                    break

                prompt = scenario.render(
                    cell, rng,
                    swept_field=cfg.SWEEP_VAR,
                    swept_idx=phrasing_idx,
                    fix_nuisance=cfg.FIX_NUISANCE_WORDING,
                )

                row: dict = {
                    "run_id": f"{level}-{phrasing_idx}-{rep}",
                    "sweep": sweep_name,
                    "scenario": cfg.SCENARIO,
                    "model": cfg.MODEL,
                    "level": level,
                    "phrasing_idx": phrasing_idx,
                    "rep": rep,
                    "prompt": prompt,
                    "oracle_at_reference": oracle_ref,
                    "oracle_at_inferred": None,
                    "reasoning": None,
                    "blameworthiness": None,
                    "inferred_probability": None,
                    "latency": None,
                    "raw": None,
                    "error": None,
                }

                if dry_run:
                    row["error"] = "dry_run"
                else:
                    from engine import client  # imported lazily so --dry needs no API key
                    try:
                        resp = client.call_model(
                            prompt, model=cfg.MODEL, temperature=cfg.TEMPERATURE,
                        )
                        row["reasoning"] = resp["reasoning"]
                        row["blameworthiness"] = resp["blameworthiness"]
                        row["inferred_probability"] = resp["inferred_probability"]
                        row["latency"] = resp["latency"]
                        row["raw"] = resp["raw"]
                        row["oracle_at_inferred"] = oracle.oracle_blame(
                            cell, p0_value=resp["inferred_probability"] / 100,
                        )
                    except Exception as exc:  # noqa: BLE001 - log, don't abort the sweep
                        row["error"] = f"{type(exc).__name__}: {exc}"
                    n_calls += 1

                _append_jsonl(raw_path, row)
                rows.append(row)

    df = pd.DataFrame(rows)
    parsed_path = RESULTS_DIR / f"parsed_{tag}.csv"
    df[_CSV_COLUMNS].to_csv(parsed_path, index=False)

    ok = df["error"].isna().sum()
    print(f"\n{'DRY RUN: ' if dry_run else ''}{len(df)} cells "
          f"({ok} successful calls) across {len(cfg.LEVELS)} levels.")
    print(f"  raw    -> {raw_path}")
    print(f"  parsed -> {parsed_path}")
    if dry_run and rows:
        print("\n=== SAMPLE RENDERED PROMPT (level="
              f"{rows[0]['level']}, phrasing_idx={rows[0]['phrasing_idx']}) ===\n")
        print(rows[0]["prompt"])
        print("\n=== ORACLE (reference values) BY LEVEL ===")
        for level in cfg.LEVELS:
            cell = Cell(**{**cfg.HELD, cfg.SWEEP_VAR: level})
            print(f"  {level:<14} db = {oracle.oracle_blame(cell):.4f}")

    return str(parsed_path)
