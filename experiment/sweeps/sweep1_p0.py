"""Sweep 1 — Epistemic optimism (belief p0).

THIS IS THE ONLY FILE YOU EDIT TO CHANGE THIS RUN.
All run knobs (model, temperature, reps, levels, held params, arms) live here.

The p0 sweep is run once per ARM. The `baseline` arm is the headline experiment;
the other arms re-run the whole p0 curve with exactly one held variable changed
(one-variable-at-a-time), to check the LLM's curve shifts the way the formal
oracle's curve shifts when that variable moves. See `run.py` for the driver that
expands models x scenarios x arms.

Run from the `experiment/` directory (single arm; use `run.py` for the grid):

    python -m sweeps.sweep1_p0                 # baseline arm, live
    python -m sweeps.sweep1_p0 --dry           # render + oracle only, no API key
    python -m sweeps.sweep1_p0 --arm vote_yes  # one named arm
    python -m sweeps.sweep1_p0 --limit 5       # cap API calls (quick live debug)
"""

from __future__ import annotations

from engine.params import Arm

# ── Run knobs ─────────────────────────────────────────────────────────────────
SCENARIO    = "s01_health"
MODEL       = "google/gemini-2.5-flash"      # OpenRouter model id (single-arm default)
TEMPERATURE = 1.0
REPS        = 10                              # repetitions per (level × phrasing)
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

# ── OFAT validation arms ────────────────────────────────────────────────────
# Each arm re-runs the whole p0 curve with one held variable changed. baseline
# is the headline run; the rest are the framework-tracking checks. One arm = one
# self-describing run directory. The driver (run.py) selects which arms to run.
ARMS = [
    Arm("baseline", {}),
    Arm("vote_yes", {"vote": "yes"}),
    Arm("alpha_negligible", {"alpha": "negligible"}),
    Arm("alpha_strong", {"alpha": "strong"}),
    Arm("cost_trivial", {"c_sw": "trivial"}),
    Arm("stakes_high", {"stakes": "high"}),
]

ARMS_BY_NAME = {a.name: a for a in ARMS}


if __name__ == "__main__":
    import argparse
    import sys

    from engine import runner

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true",
                    help="render prompts + compute oracle only; no API calls")
    ap.add_argument("--arm", default="baseline", choices=list(ARMS_BY_NAME),
                    help="which OFAT arm to run (default: baseline)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of API calls (live debugging)")
    args = ap.parse_args()

    cfg = sys.modules[__name__]
    arm = ARMS_BY_NAME[args.arm]

    if args.dry:
        runner.run(cfg, arm=arm, dry_run=True, limit=args.limit)
        sys.exit(0)

    from tqdm.auto import tqdm
    total = runner.count_planned(cfg, arm=arm, scenario=SCENARIO, limit=args.limit)
    bar = tqdm(total=total, unit="call", desc=f"{SCENARIO}/{arm.name}", smoothing=0.05)
    try:
        runner.run(cfg, arm=arm, limit=args.limit,
                   on_progress=bar.update, verbose=False)
    except KeyboardInterrupt:
        bar.close()
        print("\ninterrupted. progress is saved; re-run to resume.")
        sys.exit(130)
    bar.close()
