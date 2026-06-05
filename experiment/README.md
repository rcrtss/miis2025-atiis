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
├── run.py              grid/OFAT driver: models x scenarios x arms in one command
├── results/            one dir per run; flat legacy files under results/_legacy/
│   └── sweep1_p0/s01_health/<model>/<arm>/<UTC-stamp>/
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
python -m run --validation --models nemotron --limit 5   # quick live smoke
```

Each run writes `results/<sweep>/<scenario>/<model>/<arm>/<UTC-stamp>/` with a
`manifest.json` (the full run config plus the oracle constants in force),
`rows.jsonl` (full log), and `rows.csv` (tidy). Then open `analysis/analysis.ipynb`.

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
