"""Generic sweep runner.

Reads a sweep-config module (see `sweeps/sweep1_p0.py`) and runs ONE arm of it
(the baseline by default, or an OFAT validation arm passed by the driver). It
expands every level x phrasing x repetition, calls the model, attaches both
oracle comparisons, and writes a self-describing run directory:

    results/<sweep>/<scenario>/<model-slug>/<arm>/<UTC-stamp>/
        manifest.json   full run characteristics + oracle constants in force
        rows.jsonl      full per-call log
        rows.csv        tidy columns for analysis

The runner knows nothing about any particular scenario or parameter; it only
follows `cfg.SWEEP_VAR` and the arm's overrides.
"""

from __future__ import annotations

import importlib
import json
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

import pandas as pd

from engine import config, oracle
from engine.params import Arm, Cell

# Columns kept in the tidy analysis CSV (full detail stays in the JSONL).
_CSV_COLUMNS = [
    "run_id", "sweep", "scenario", "model", "arm", "level", "phrasing_idx", "rep",
    "blameworthiness", "inferred_probability", "inferred_alpha", "inferred_cost",
    "oracle_at_reference", "oracle_at_inferred", "error",
]


def _append_jsonl(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _code_version() -> str | None:
    """Short git sha of the experiment's repo, or None if unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(config.ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


def _manifest(cfg: ModuleType, *, sweep: str, scenario: str, model: str,
              arm: Arm, stamp: str) -> dict:
    """Snapshot every run characteristic, including the oracle constants in
    force, so a result is reproducible from its own directory alone."""
    return {
        "run_id": stamp,
        "sweep": sweep,
        "sweep_var": cfg.SWEEP_VAR,
        "scenario": scenario,
        "model": model,
        "temperature": cfg.TEMPERATURE,
        "reps": cfg.REPS,
        "seed": cfg.SEED,
        "levels": list(cfg.LEVELS),
        "arm": arm.name,
        "arm_overrides": dict(arm.overrides),
        "held": dict(cfg.HELD),
        "fix_nuisance_wording": cfg.FIX_NUISANCE_WORDING,
        "oracle": {
            "n_balance": oracle.N_BALANCE,
            "c_pressure": oracle.C_PRESSURE,
            "stakes_n_reference": dict(oracle.STAKES_N_REFERENCE),
            "p0_reference": dict(oracle.P0_REFERENCE),
            "csw_reference": dict(oracle.CSW_REFERENCE),
            "alpha_reference": dict(oracle.ALPHA_REFERENCE),
        },
        "code_version": _code_version(),
        "started_utc": stamp,
    }


def run(
    cfg: ModuleType,
    *,
    arm: Arm | None = None,
    scenario: str | None = None,
    model: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> str:
    """Execute one arm of the sweep `cfg`. Returns the run directory path.

    `arm`, `scenario`, `model` override the sweep defaults (the driver supplies
    them when expanding the grid); omitted, they fall back to the baseline arm
    and the sweep's own SCENARIO/MODEL.
    """
    arm = arm if arm is not None else Arm("baseline", {})
    scenario = scenario if scenario is not None else cfg.SCENARIO
    model = model if model is not None else cfg.MODEL

    scenario_mod = importlib.import_module(f"prompts.{scenario}.scenario")
    # Placeholder scenarios ship an empty TEMPLATE/PHRASINGS; surface that as a
    # clean NotImplementedError so the driver can skip rather than crash later.
    if not getattr(scenario_mod, "TEMPLATE", "") or not getattr(scenario_mod, "PHRASINGS", {}):
        raise NotImplementedError(f"scenario '{scenario}' is not implemented")
    rng = random.Random(cfg.SEED)

    # When launched via `python -m`, cfg.__name__ is "__main__"; use the filename.
    sweep_name = Path(getattr(cfg, "__file__", cfg.__name__)).stem
    model_slug = model.split("/")[-1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    out_dir = config.run_dir(sweep_name, scenario, model_slug, arm.name, stamp)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "rows.jsonl"

    rows: list[dict] = []
    n_calls = 0

    for level in cfg.LEVELS:
        cell = Cell(**{**cfg.HELD, **arm.overrides, cfg.SWEEP_VAR: level})
        oracle_ref = oracle.oracle_blame(cell)
        n_phrasings = len(scenario_mod.PHRASINGS[cfg.SWEEP_VAR][level])

        for phrasing_idx in range(n_phrasings):
            for rep in range(cfg.REPS):
                if limit is not None and n_calls >= limit:
                    break

                prompt = scenario_mod.render(
                    cell, rng,
                    swept_field=cfg.SWEEP_VAR,
                    swept_idx=phrasing_idx,
                    fix_nuisance=cfg.FIX_NUISANCE_WORDING,
                )

                row: dict = {
                    "run_id": f"{arm.name}-{level}-{phrasing_idx}-{rep}",
                    "sweep": sweep_name,
                    "scenario": scenario,
                    "model": model,
                    "arm": arm.name,
                    "level": level,
                    "phrasing_idx": phrasing_idx,
                    "rep": rep,
                    "prompt": prompt,
                    "oracle_at_reference": oracle_ref,
                    "oracle_at_inferred": None,
                    "reasoning": None,
                    "blameworthiness": None,
                    "inferred_probability": None,
                    "inferred_alpha": None,
                    "inferred_cost": None,
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
                            prompt, model=model, temperature=cfg.TEMPERATURE,
                        )
                        row["reasoning"] = resp["reasoning"]
                        row["blameworthiness"] = resp["blameworthiness"]
                        row["inferred_probability"] = resp["inferred_probability"]
                        row["inferred_alpha"] = resp["inferred_alpha"]
                        row["inferred_cost"] = resp["inferred_cost"]
                        row["latency"] = resp["latency"]
                        row["raw"] = resp["raw"]
                        cost_ratio = (
                            None if resp["inferred_cost"] is None
                            else resp["inferred_cost"] / 100
                        )
                        row["oracle_at_inferred"] = oracle.oracle_blame(
                            cell,
                            p0_value=resp["inferred_probability"] / 100,
                            alpha_value=resp["inferred_alpha"] / 100,
                            csw_over_N=cost_ratio,
                        )
                    except Exception as exc:  # noqa: BLE001 - log, don't abort the sweep
                        row["error"] = f"{type(exc).__name__}: {exc}"
                    n_calls += 1

                _append_jsonl(raw_path, row)
                rows.append(row)

    df = pd.DataFrame(rows)
    parsed_path = out_dir / "rows.csv"
    df[_CSV_COLUMNS].to_csv(parsed_path, index=False)

    n_errors = int(df["error"].notna().sum()) if not dry_run else 0
    manifest = _manifest(
        cfg, sweep=sweep_name, scenario=scenario, model=model, arm=arm, stamp=stamp,
    )
    manifest["n_calls"] = n_calls
    manifest["n_errors"] = n_errors
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    ok = int(df["error"].isna().sum())
    print(f"\n{'DRY RUN: ' if dry_run else ''}[{arm.name}] {len(df)} cells "
          f"({ok} ok) across {len(cfg.LEVELS)} levels  ->  {out_dir}")
    if dry_run and rows:
        print("\n=== SAMPLE RENDERED PROMPT (level="
              f"{rows[0]['level']}, phrasing_idx={rows[0]['phrasing_idx']}) ===\n")
        print(rows[0]["prompt"])
        print("\n=== ORACLE (reference values) BY LEVEL ===")
        for level in cfg.LEVELS:
            cell = Cell(**{**cfg.HELD, **arm.overrides, cfg.SWEEP_VAR: level})
            print(f"  {level:<14} db = {oracle.oracle_blame(cell):.4f}")

    return str(out_dir)
