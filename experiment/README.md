# Experiment — LLM moral reasoning under formal blameworthiness

Probes whether an LLM's blame judgments track the *counterfactual structure* of a
collective decision (what `framework/committee.py` computes) or only its
*surface action*. The experiment is the belief (`p0`) sweep; the other variables
(`vote`, `alpha`, `c_sw`/`stakes`) are run as one-variable-at-a-time validation
arms that check the LLM curve shifts the way the oracle curve shifts. See
[`DESIGN.md`](./DESIGN.md) for the full design.

## Layout

```
experiment/
├── DESIGN.md            master design (p0 sweep + validation arms; deferred sweeps)
├── engine/              scenario-agnostic machinery
│   ├── params.py        Cell (one condition, number-free) + Arm (one OFAT arm)
│   ├── config.py        fixed plumbing (API URL, results path + run_dir helper)
│   ├── oracle.py        Shapley oracle; the ONLY place ordinal ids -> numbers
│   ├── client.py        OpenRouter over httpx (no SDK) + retry + JSON validation
│   └── runner.py        runs ONE arm -> one self-describing run directory
├── prompts/             scenario CONTENT only (one per domain)
│   ├── s01_health/       hospital authorization (weighty, identified victim)
│   ├── s02_grant/         grant-review panel (weighty, statistical victim)
│   └── s03_board/         corporate board (cold, no human victim)
├── sweeps/
│   └── sweep1_p0.py     the file you edit per run (model, reps, levels, ARMS)
├── run.py              grid/OFAT driver: models x scenarios x arms, with a
│                       progress bar and resume-on-cancel
├── results/            one stable dir per run; flat legacy files under results/_legacy/
│   └── sweep1_p0/s01_health/<model>/<arm>/
│           manifest.json  rows.jsonl  rows.csv
└── analysis/
    ├── loader.py        globs manifests into one tidy DataFrame
    └── analysis.ipynb   comparative stats + report-ready figures/tables
```

## Setup

Deps are pinned in `requirements.txt` (`statsmodels` is optional, only for the
extra mixed-model cell). For live runs, add your key:

```bash
cp experiment/.env.example experiment/.env   # then edit OPENROUTER_API_KEY
```

## Run (from the `experiment/` directory)

One arm at a time via the sweep module:

```bash
python -m sweeps.sweep1_p0 --dry              # render prompts + oracle, no API key
python -m sweeps.sweep1_p0 --arm vote_yes     # one named arm
python -m sweeps.sweep1_p0 --limit 5          # quick live smoke test
```

The whole grid via the driver:

```bash
python -m run --headline                      # baseline arm, all models x all scenarios
python -m run --validation                    # all arms, all models x s01
python -m run --headline --validation         # both (shared baseline x s01 runs once)
python -m run --validation --models gemini --limit 5     # quick live smoke
python -m run --headline --concurrency 8      # 8 calls in parallel per run (much faster)
```

`--concurrency N` issues N model calls at once (they are network-bound); results
are still written in the main thread, so resume/checkpoint semantics are
unchanged. Because each (model, scenario, arm) writes its own stable directory,
you can also shard across processes safely, e.g. one model each in parallel:

```bash
for m in qwen gemini llama; do
  python -m run --headline --models $m --concurrency 8 &
done
wait
```

Each run writes a stable `results/<sweep>/<scenario>/<model>/<arm>/` directory
with a `manifest.json` (full run config + oracle constants + `status`),
`rows.jsonl` (append-only per-call log), and `rows.csv` (tidy). Then open
`analysis/analysis.ipynb`.

**Progress and resume.** `run.py` shows a single progress bar over all planned
calls across the grid. Results stream to `rows.jsonl` as they complete, so if you
cancel (Ctrl-C) or the run dies, nothing is lost: re-run the exact same command
and it skips the calls already done, retries any that errored, and continues. The
stable (timestamp-free) directory is what makes this work; run timestamps and
completion `status` live inside `manifest.json`. For the report, load with
`load_runs(complete_only=True)` to exclude any half-finished run.

## Design notes baked into the code

- **No numbers in prompts.** Subjective parameters (belief, cost, lobbying
  effect) are ordinal ids mapped to natural-language wordings. The probability
  and cost numbers exist only in `engine/oracle.py`, flagged as a *reference* for
  the formal calculation, never as a claim that a wording equals a value. That
  mapping is what the experiment tests.
- **Per-call inference.** Every call returns the model's own reading of `p0`
  (`inferred_probability`), `alpha` (`inferred_alpha`), and, for a no-voter, the
  switch cost as a percent of stakes (`inferred_cost`).
- **Two oracle comparisons per call.** `oracle_at_reference` (our nominal
  mapping) and `oracle_at_inferred` (committee.py fed the model's own inferred
  values for `p0`, `alpha`, and cost; assumption-free).
- **One arm = one run directory.** The manifest makes each run reproducible from
  its own folder, so run provenance lives in data, not in filenames.
- **Adding a scenario** = a new `prompts/sXX/scenario.py` exposing `TEMPLATE`,
  `PHRASINGS`, `render`. The engine is content-blind.
