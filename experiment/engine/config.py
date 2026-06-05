"""Cross-sweep constants that are NOT tuning knobs.

Run knobs (model, temperature, reps, levels, ...) live in `sweeps/<sweep>.py`,
the one file you edit per run. This module only holds fixed plumbing: where the
API lives and where results land. Keeping them here means they are in one place,
not scattered through the code.
"""

from __future__ import annotations

from pathlib import Path

# OpenRouter is plain REST; we call it directly over httpx (see engine/client.py).
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# experiment/  (this file is experiment/engine/config.py)
ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def run_dir(sweep: str, scenario: str, model_slug: str, arm: str) -> Path:
    """Self-describing path for one run's artifacts.

    Layout: results/<sweep>/<scenario>/<model-slug>/<arm>/ holding manifest.json
    + rows.jsonl + rows.csv. The path is STABLE per (sweep, scenario, model, arm)
    with no per-run timestamp, so an interrupted run resumes into the same place
    instead of starting a fresh empty directory. Run timestamps live inside
    manifest.json. Nesting by run characteristics (not a stringy filename) is what
    keeps the growing result set navigable.
    """
    return RESULTS_DIR / sweep / scenario / model_slug / arm
