"""Sweep 1 — Epistemic optimism (belief p0).

THIS IS THE ONLY FILE YOU EDIT TO CHANGE THIS RUN.
All run knobs (model, temperature, reps, levels, held params) live here.

Run from the `experiment/` directory:

    python -m sweeps.sweep1_p0            # live run against the API
    python -m sweeps.sweep1_p0 --dry      # render + oracle only, no API key needed
    python -m sweeps.sweep1_p0 --limit 5  # cap API calls (quick live debug)
"""

from __future__ import annotations

# ── Run knobs ─────────────────────────────────────────────────────────────────
SCENARIO    = "s01_health"
MODEL       = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"   # OpenRouter model id
TEMPERATURE = 1.0
REPS        = 15                              # repetitions per (level × phrasing)
SEED        = 0                               # reproducible nuisance sampling

# ── What this sweep varies ──────────────────────────────────────────────────
SWEEP_VAR = "p0"
LEVELS = [
    "very_low", "low", "somewhat_low", "even", "somewhat_high", "high", "very_high",
]

# ── What it holds fixed (every Cell field except SWEEP_VAR) ─────────────────
HELD = {
    "c_sw": "significant",   # ~paper baseline switch cost
    "alpha": "modest",       # ~paper baseline pressure effectiveness
    "vote": "no",            # focal agent voted no
    "stakes": "default",     # valence-neutral framing
    "num_agents": 7,
    "pass_threshold": 4,
}

# Vary only the swept variable's wording; fix all other wordings to reduce
# nuisance variance. Set False to also randomize held-parameter phrasings.
FIX_NUISANCE_WORDING = True

# Generic hook for later robustness checks (e.g. {"vote": ["no", "yes"]} or
# {"c_sw": ["minor", "severe"]}). None now -> clean 1-D p0 sweep.
SECONDARY_AXIS = None


if __name__ == "__main__":
    import argparse
    import sys

    from engine import runner

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true",
                    help="render prompts + compute oracle only; no API calls")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of API calls (live debugging)")
    args = ap.parse_args()

    runner.run(sys.modules[__name__], dry_run=args.dry, limit=args.limit)
