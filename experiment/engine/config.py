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
