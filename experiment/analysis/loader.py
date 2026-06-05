"""Manifest-driven result loader for the analysis notebook.

Discovers every run by its `manifest.json` (never by parsing filenames), joins
the manifest's run characteristics onto its tidy `rows.csv`, and returns one long
DataFrame across all runs. One row per model call.

Usage:

    from analysis.loader import load_runs, P0_LEVEL_ORDER
    df = load_runs()                      # everything under results/
    df = load_runs(sweep="sweep1_p0")     # one sweep
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from engine.config import RESULTS_DIR

# Canonical ordinal order of the p0 levels (low optimism -> high optimism).
P0_LEVEL_ORDER = [
    "very_low", "low", "somewhat_low", "even", "somewhat_high", "high", "very_high",
]

# Manifest fields promoted onto every row (run-level metadata for grouping).
_MANIFEST_COLS = [
    "run_id", "sweep_var", "temperature", "reps", "seed", "code_version",
    "n_calls", "n_errors", "started_utc",
]


def _load_one(manifest_path: Path) -> pd.DataFrame | None:
    """Join one run's rows.csv with its manifest. Returns None if rows missing."""
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    rows_path = manifest_path.parent / "rows.csv"
    if not rows_path.exists():
        return None
    df = pd.read_csv(rows_path)
    if df.empty:
        return None

    for col in _MANIFEST_COLS:
        df[col] = manifest.get(col)

    # Numeric x-axis for p0: the reference probability each level maps to.
    p0_ref = manifest.get("oracle", {}).get("p0_reference", {})
    if manifest.get("sweep_var") == "p0":
        df["level_value"] = df["level"].map(p0_ref)
        df["level"] = pd.Categorical(df["level"], categories=P0_LEVEL_ORDER, ordered=True)
        df["level_rank"] = df["level"].cat.codes
    return df


def load_runs(results_dir: Path | str = RESULTS_DIR, *, sweep: str | None = None,
              drop_errors: bool = True) -> pd.DataFrame:
    """Load all runs into one tidy long DataFrame.

    `sweep` restricts to one sweep subtree (e.g. "sweep1_p0"). `drop_errors`
    removes calls that failed (non-null `error`); the manifest's `n_errors`
    still records how many there were.
    """
    root = Path(results_dir)
    base = root / sweep if sweep else root
    frames = [d for p in sorted(base.rglob("manifest.json")) if (d := _load_one(p)) is not None]
    if not frames:
        raise FileNotFoundError(f"no runs with rows.csv found under {base}")

    df = pd.concat(frames, ignore_index=True)
    if drop_errors and "error" in df.columns:
        df = df[df["error"].isna()].copy()

    # Short model name for legends/tables.
    df["model_slug"] = df["model"].str.split("/").str[-1]
    return df
