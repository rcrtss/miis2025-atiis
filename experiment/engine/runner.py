"""Generic sweep runner (resumable).

Reads a sweep-config module (see `sweeps/sweep1_p0.py`) and runs ONE arm of it
(the baseline by default, or an OFAT validation arm passed by the driver). It
expands every level x phrasing x repetition, calls the model, attaches both
oracle comparisons, and writes a self-describing run directory:

    results/<sweep>/<scenario>/<model-slug>/<arm>/
        manifest.json   full run characteristics + oracle constants + status
        rows.jsonl      append-only per-call log (the durable record)
        rows.csv        tidy columns for analysis (rebuilt at each checkpoint)

The directory is STABLE per (sweep, scenario, model, arm): there is no per-run
timestamp in the path. That is what makes runs resumable. If a run is cancelled
(Ctrl-C) or dies, the calls already streamed to `rows.jsonl` survive; re-running
the same command reloads them, skips the completed calls, retries the failed or
missing ones, and continues. Timestamps live inside `manifest.json` instead.

The runner knows nothing about any particular scenario or parameter; it only
follows `cfg.SWEEP_VAR` and the arm's overrides.
"""

from __future__ import annotations

import importlib
import json
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Callable

import pandas as pd

from engine import config, oracle
from engine.params import Arm, Cell

# Columns kept in the tidy analysis CSV (full detail stays in the JSONL).
_CSV_COLUMNS = [
    "run_id", "sweep", "scenario", "model", "arm", "level", "phrasing_idx", "rep",
    "blameworthiness", "inferred_probability", "inferred_alpha", "inferred_cost",
    "oracle_at_reference", "oracle_at_inferred", "error",
]

# How many freshly executed calls between checkpoint rewrites of rows.csv +
# manifest.json. The jsonl is written per-call regardless, so a smaller number
# only buys a fresher derived CSV at the cost of more rewrites.
CHECKPOINT_EVERY = 20

ProgressFn = Callable[[int], None]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def _load_ready_scenario(scenario: str) -> ModuleType:
    """Import a scenario module, raising NotImplementedError if it is a stub
    (empty TEMPLATE/PHRASINGS) so the driver can skip rather than crash later."""
    mod = importlib.import_module(f"prompts.{scenario}.scenario")
    if not getattr(mod, "TEMPLATE", "") or not getattr(mod, "PHRASINGS", {}):
        raise NotImplementedError(f"scenario '{scenario}' is not implemented")
    return mod


def _plan(cfg: ModuleType, scenario_mod: ModuleType, arm: Arm,
          limit: int | None) -> list[tuple]:
    """Flatten the whole arm into an ordered list of planned calls.

    Each item is (level, cell, oracle_ref, phrasing_idx, rep, run_id). Flattening
    (rather than nested loops) makes `limit` a clean slice and gives the driver an
    exact total for the progress bar.
    """
    items: list[tuple] = []
    for level in cfg.LEVELS:
        cell = Cell(**{**cfg.HELD, **arm.overrides, cfg.SWEEP_VAR: level})
        oracle_ref = oracle.oracle_blame(cell)
        n_phrasings = len(scenario_mod.PHRASINGS[cfg.SWEEP_VAR][level])
        for phrasing_idx in range(n_phrasings):
            for rep in range(cfg.REPS):
                run_id = f"{arm.name}-{level}-{phrasing_idx}-{rep}"
                items.append((level, cell, oracle_ref, phrasing_idx, rep, run_id))
    if limit is not None:
        items = items[:limit]
    return items


def count_planned(cfg: ModuleType, *, arm: Arm, scenario: str,
                  limit: int | None = None) -> int:
    """Number of calls one arm would make. Returns 0 for stub scenarios so the
    driver can total the grid without crashing on not-yet-implemented skins."""
    try:
        scenario_mod = _load_ready_scenario(scenario)
    except NotImplementedError:
        return 0
    return len(_plan(cfg, scenario_mod, arm, limit))


def _load_existing(raw_path: Path) -> dict[str, dict]:
    """Reload a prior (possibly interrupted) run's rows from its jsonl, keyed by
    run_id, last write wins. A partial final line from a crash is skipped."""
    merged: dict[str, dict] = {}
    if not raw_path.exists():
        return merged
    with open(raw_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # truncated last line from an abrupt kill
            rid = row.get("run_id")
            if rid is not None:
                merged[rid] = row
    return merged


def _manifest_base(cfg: ModuleType, *, sweep: str, scenario: str, model: str,
                   arm: Arm, started: str) -> dict:
    """Static run characteristics, including the oracle constants in force, so a
    result is reproducible from its own directory alone."""
    return {
        "run_id": f"{sweep}/{scenario}/{model.split('/')[-1]}/{arm.name}",
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
        "started_utc": started,
    }


def _write_checkpoint(out_dir: Path, plan: list[tuple], merged: dict[str, dict],
                      base: dict, *, status: str) -> None:
    """Rebuild rows.csv from the merged rows (in plan order) and write manifest
    with the current status and counts. Safe to call repeatedly."""
    ordered = [merged[rid] for *_, rid in plan if rid in merged]
    df = pd.DataFrame(ordered)
    for col in _CSV_COLUMNS:           # guarantee columns even on an empty run
        if col not in df.columns:
            df[col] = None
    df[_CSV_COLUMNS].to_csv(out_dir / "rows.csv", index=False)

    n_attempted = len(ordered)
    n_errors = int(sum(1 for r in ordered if r.get("error") is not None))
    manifest = dict(base)
    manifest.update({
        "status": status,                 # in_progress | interrupted | complete
        "updated_utc": _now(),
        "n_planned": len(plan),
        "n_calls": n_attempted,
        "n_done": n_attempted - n_errors,
        "n_errors": n_errors,
    })
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)


def _execute_one(scenario_mod: ModuleType, cfg: ModuleType, client, item: tuple,
                 *, sweep_name: str, scenario: str, model: str, arm: Arm,
                 started: str) -> tuple[str, dict]:
    """Render one prompt, call the model, attach both oracle comparisons, and
    return (run_id, row). Pure and self-contained (no shared mutable state and no
    file I/O) so it is safe to run in a worker thread; all writing happens back in
    the main thread. A failed call is logged in the row, never raised, so one bad
    call cannot abort the pool.
    """
    level, cell, oracle_ref, phrasing_idx, rep, run_id = item

    # Per-call deterministic RNG so resume is exact regardless of which calls were
    # already done or of completion order under concurrency.
    rng = random.Random(f"{cfg.SEED}-{run_id}")
    prompt = scenario_mod.render(
        cell, rng, swept_field=cfg.SWEEP_VAR, swept_idx=phrasing_idx,
        fix_nuisance=cfg.FIX_NUISANCE_WORDING,
    )

    row: dict = {
        "run_id": run_id, "sweep": sweep_name, "scenario": scenario,
        "model": model, "arm": arm.name, "level": level,
        "phrasing_idx": phrasing_idx, "rep": rep, "prompt": prompt,
        "oracle_at_reference": oracle_ref, "oracle_at_inferred": None,
        "reasoning": None, "blameworthiness": None,
        "inferred_probability": None, "inferred_alpha": None,
        "inferred_cost": None, "latency": None, "raw": None,
        "error": None, "started_utc": started,
    }

    try:
        resp = client.call_model(prompt, model=model, temperature=cfg.TEMPERATURE)
        row["reasoning"] = resp["reasoning"]
        row["blameworthiness"] = resp["blameworthiness"]
        row["inferred_probability"] = resp["inferred_probability"]
        row["inferred_alpha"] = resp["inferred_alpha"]
        row["inferred_cost"] = resp["inferred_cost"]
        row["latency"] = resp["latency"]
        row["raw"] = resp["raw"]
        cost_ratio = (None if resp["inferred_cost"] is None
                      else resp["inferred_cost"] / 100)
        row["oracle_at_inferred"] = oracle.oracle_blame(
            cell,
            p0_value=resp["inferred_probability"] / 100,
            alpha_value=resp["inferred_alpha"] / 100,
            csw_over_N=cost_ratio,
        )
    except Exception as exc:  # noqa: BLE001 - log, keep going, retry on next run
        row["error"] = f"{type(exc).__name__}: {exc}"
    return run_id, row


def run(
    cfg: ModuleType,
    *,
    arm: Arm | None = None,
    scenario: str | None = None,
    model: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    on_progress: ProgressFn | None = None,
    verbose: bool = True,
    concurrency: int = 1,
) -> str | None:
    """Execute one arm of the sweep `cfg`, resuming any prior partial run.

    `arm`, `scenario`, `model` override the sweep defaults (the driver supplies
    them when expanding the grid). `on_progress(n)` is called once per planned
    call (whether skipped-as-already-done or freshly executed) so a caller can
    drive a global progress bar. `verbose` prints a per-run summary; the driver
    sets it False and reports via the bar. `concurrency` issues that many model
    calls at once via a thread pool (the calls are network-bound); results are
    still collected and written in the main thread, so the jsonl/checkpoint/resume
    logic is unchanged and lock-free. `concurrency=1` is the plain serial path.
    Returns the run directory path (None for a dry run, which writes nothing).
    """
    arm = arm if arm is not None else Arm("baseline", {})
    scenario = scenario if scenario is not None else cfg.SCENARIO
    model = model if model is not None else cfg.MODEL

    scenario_mod = _load_ready_scenario(scenario)   # raises for stub scenarios
    sweep_name = Path(getattr(cfg, "__file__", cfg.__name__)).stem
    model_slug = model.split("/")[-1]
    plan = _plan(cfg, scenario_mod, arm, limit)

    # ── Dry run: render + oracle only, no writes, no API key ──────────────────
    if dry_run:
        if on_progress:
            on_progress(len(plan))
        if verbose and plan:
            level, cell, _ref, phrasing_idx, _rep, _rid = plan[0]
            rng = random.Random(f"{cfg.SEED}-{plan[0][5]}")
            prompt = scenario_mod.render(
                cell, rng, swept_field=cfg.SWEEP_VAR, swept_idx=phrasing_idx,
                fix_nuisance=cfg.FIX_NUISANCE_WORDING,
            )
            print(f"\nDRY RUN: [{arm.name}] {scenario} @ {model}  "
                  f"({len(plan)} planned calls, nothing written)")
            print(f"\n=== SAMPLE RENDERED PROMPT (level={level}, "
                  f"phrasing_idx={phrasing_idx}) ===\n")
            print(prompt)
            print("\n=== ORACLE (reference values) BY LEVEL ===")
            for lvl in cfg.LEVELS:
                c = Cell(**{**cfg.HELD, **arm.overrides, cfg.SWEEP_VAR: lvl})
                print(f"  {lvl:<14} db = {oracle.oracle_blame(c):.4f}")
        return None

    # ── Live run: resumable ───────────────────────────────────────────────────
    out_dir = config.run_dir(sweep_name, scenario, model_slug, arm.name)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "rows.jsonl"

    merged = _load_existing(raw_path)
    started = merged.get(next(iter(merged), None), {}).get("started_utc") or _now()
    base = _manifest_base(cfg, sweep=sweep_name, scenario=scenario, model=model,
                          arm=arm, started=started)

    def is_done(rid: str) -> bool:
        r = merged.get(rid)
        return (r is not None and r.get("error") is None
                and r.get("blameworthiness") is not None)

    # Split the plan: already-finished calls just advance the bar; the rest are
    # the work for this run (missing or previously errored, so retried).
    todo: list[tuple] = []
    n_skipped = 0
    for item in plan:
        if is_done(item[5]):
            n_skipped += 1
            if on_progress:
                on_progress(1)
        else:
            todo.append(item)

    from engine import client  # lazy: --dry needs no API key

    # Consume one finished result in the MAIN thread: append, merge, checkpoint.
    # Keeping all writes here means the resume logic needs no locks even with a
    # thread pool feeding results in.
    state = {"new": 0}

    def consume(run_id: str, row: dict) -> None:
        _append_jsonl(raw_path, row)
        merged[run_id] = row
        if on_progress:
            on_progress(1)
        state["new"] += 1
        if state["new"] >= CHECKPOINT_EVERY:
            _write_checkpoint(out_dir, plan, merged, base, status="in_progress")
            state["new"] = 0

    def work(item: tuple) -> tuple[str, dict]:
        return _execute_one(scenario_mod, cfg, client, item, sweep_name=sweep_name,
                            scenario=scenario, model=model, arm=arm, started=started)

    workers = max(1, int(concurrency))
    try:
        if workers == 1:
            for item in todo:
                run_id, row = work(item)
                consume(run_id, row)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = [ex.submit(work, item) for item in todo]
                try:
                    for fut in as_completed(futures):
                        run_id, row = fut.result()
                        consume(run_id, row)
                except KeyboardInterrupt:
                    # Drop not-yet-started calls; in-flight ones finish in the
                    # background (their results are simply discarded and retried).
                    ex.shutdown(wait=False, cancel_futures=True)
                    raise
    except KeyboardInterrupt:
        _write_checkpoint(out_dir, plan, merged, base, status="interrupted")
        raise

    _write_checkpoint(out_dir, plan, merged, base, status="complete")

    if verbose:
        attempted = sum(1 for *_, rid in plan if rid in merged)
        errs = sum(1 for *_, rid in plan
                   if rid in merged and merged[rid].get("error") is not None)
        print(f"\n[{arm.name}] {scenario} @ {model_slug}: {attempted} cells "
              f"({attempted - errs} ok, {n_skipped} resumed)  ->  {out_dir}")
    return str(out_dir)
