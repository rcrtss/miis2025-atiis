"""Grid / OFAT driver: run a sweep across models x scenarios x arms.

This is the one command to launch experiments. It expands a set of
(model, scenario, arm) combinations and calls `engine.runner.run` once per
combination, each producing its own self-describing run directory. The sweep
module (default `sweeps.sweep1_p0`) supplies the levels, held params, and the
ARMS catalogue; this driver only chooses which combinations to run.

Run from the `experiment/` directory:

    python -m run --headline                 # baseline arm, all models x all scenarios
    python -m run --validation               # all arms, all models x s01 only
    python -m run --headline --validation    # both (the shared baseline x s01 runs once)
    python -m run --validation --models nemotron --limit 5   # quick live smoke
    python -m run --headline --dry           # render + oracle only, no API key

Custom grids (when neither --headline nor --validation is given):

    python -m run --models gemini,qwen --scenarios s01_health --arms baseline,vote_yes
"""

from __future__ import annotations

import argparse
import importlib
from itertools import product

from tqdm.auto import tqdm

from engine import runner

# OpenRouter model ids, keyed by short name. Edit these to add/swap models.
MODELS: dict[str, str] = {
    "qwen":   "qwen/qwen3-235b-a22b-2507",       # large open instruct (anchor)
    "gemini": "google/gemini-2.5-flash",         # mid, fast
    "llama":  "meta-llama/llama-3.3-70b-instruct",  # open, lower tier
}

# Scenario skins. All three are implemented; the driver still skips any scenario
# that raises NotImplementedError, so a partial grid keeps running.
ALL_SCENARIOS = ["s01_health", "s02_grant", "s03_board"]

# Validation arms run on this scenario only (per the re-scoped design).
VALIDATION_SCENARIOS = ["s01_health"]


def _resolve_models(spec: str | None) -> list[str]:
    """Map a comma list of short names (or 'all') to OpenRouter model ids."""
    if spec is None or spec == "all":
        return list(MODELS.values())
    ids = []
    for name in spec.split(","):
        name = name.strip()
        if name in MODELS:
            ids.append(MODELS[name])
        elif "/" in name:          # allow passing a full model id directly
            ids.append(name)
        else:
            raise SystemExit(f"unknown model '{name}'; known: {', '.join(MODELS)}")
    return ids


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep", default="sweep1_p0", help="sweep module under sweeps/")
    ap.add_argument("--headline", action="store_true",
                    help="baseline arm across all models x all scenarios")
    ap.add_argument("--validation", action="store_true",
                    help="all arms across all models x the validation scenario(s)")
    ap.add_argument("--models", default=None,
                    help="comma list of short names or 'all' (default: all)")
    ap.add_argument("--scenarios", default=None,
                    help="comma list (custom grid only)")
    ap.add_argument("--arms", default=None,
                    help="comma list or 'all' (custom grid only)")
    ap.add_argument("--dry", action="store_true",
                    help="render prompts + compute oracle only; no API calls")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap API calls per run (live debugging)")
    ap.add_argument("--concurrency", type=int, default=1,
                    help="model calls to issue in parallel per run (default 1)")
    args = ap.parse_args()

    cfg = importlib.import_module(f"sweeps.{args.sweep}")
    models = _resolve_models(args.models)
    all_arms = list(cfg.ARMS_BY_NAME)

    # Build a de-duplicated set of (model_id, scenario, arm_name) combinations.
    combos: set[tuple[str, str, str]] = set()
    if args.headline:
        for m, s in product(models, ALL_SCENARIOS):
            combos.add((m, s, "baseline"))
    if args.validation:
        for m, s, arm in product(models, VALIDATION_SCENARIOS, all_arms):
            combos.add((m, s, arm))
    if not args.headline and not args.validation:
        scenarios = (args.scenarios.split(",") if args.scenarios
                     else VALIDATION_SCENARIOS)
        arms = (all_arms if args.arms in (None, "all")
                else [a.strip() for a in args.arms.split(",")])
        for m, s, arm in product(models, [s.strip() for s in scenarios], arms):
            combos.add((m, s, arm))

    if not combos:
        raise SystemExit("no combinations selected; see --help")

    ordered = sorted(combos)
    print(f"sweep={args.sweep}  runs={len(ordered)}  dry={args.dry}  limit={args.limit}")

    # Dry runs make no API calls, so a per-call progress bar is meaningless; just
    # render each combo and return.
    if args.dry:
        for model_id, scenario, arm_name in ordered:
            try:
                runner.run(cfg, arm=cfg.ARMS_BY_NAME[arm_name], scenario=scenario,
                           model=model_id, dry_run=True, limit=args.limit)
            except NotImplementedError:
                print(f"SKIP [{arm_name}] {scenario} @ {model_id}: not implemented")
        return

    # Total planned calls across the whole grid drives one global bar. Resumed
    # (already-done) calls advance it too, so it reflects true completion.
    total = sum(runner.count_planned(cfg, arm=cfg.ARMS_BY_NAME[arm_name],
                                     scenario=scenario, limit=args.limit)
                for model_id, scenario, arm_name in ordered)

    bar = tqdm(total=total, unit="call", desc="experiment", smoothing=0.05)
    try:
        for model_id, scenario, arm_name in ordered:
            bar.set_postfix_str(f"{scenario}/{arm_name}@{model_id.split('/')[-1]}")
            try:
                out = runner.run(cfg, arm=cfg.ARMS_BY_NAME[arm_name], scenario=scenario,
                                 model=model_id, limit=args.limit,
                                 on_progress=bar.update, verbose=False,
                                 concurrency=args.concurrency)
            except NotImplementedError:
                tqdm.write(f"SKIP [{arm_name}] {scenario} @ {model_id}: not implemented")
                continue
            tqdm.write(f"done [{arm_name}] {scenario} @ {model_id.split('/')[-1]}  ->  {out}")
    except KeyboardInterrupt:
        bar.close()
        print("\ninterrupted. progress is saved; re-run the same command to resume "
              "from where it stopped.")
        raise SystemExit(130)
    bar.close()


if __name__ == "__main__":
    main()
