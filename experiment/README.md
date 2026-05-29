# Experiment — LLM moral reasoning under formal blameworthiness

Probes whether an LLM's blame judgments track the *counterfactual structure* of a
collective decision (what `framework/committee.py` computes) or only its
*surface action*. See [`DESIGN.md`](./DESIGN.md) for the full 6-sweep design.

## Layout

```
experiment/
├── DESIGN.md            master design (all 6 sweeps)
├── engine/              scenario-agnostic machinery
│   ├── params.py        Cell — one condition, in number-free ordinal terms
│   ├── config.py        fixed plumbing (API URL, results path)
│   ├── oracle.py        Shapley oracle; the ONLY place ordinal ids -> numbers
│   ├── client.py        OpenRouter over httpx (no SDK) + retry + JSON validation
│   └── runner.py        expands cells × phrasings × reps -> JSONL + CSV
├── prompts/             scenario CONTENT only (one per domain)
│   ├── s01_health/       hospital authorization (implemented)
│   ├── s02_placeholder/  TBD
│   └── s03_placeholder/  TBD
├── sweeps/
│   └── sweep1_p0.py     ← the ONE file you edit per run (model, reps, levels...)
├── results/            raw_*.jsonl (full) + parsed_*.csv (tidy)  [gitignored]
└── analysis/
    └── sweep1_p0.ipynb plots + Spearman vs the oracle
```

## Setup

Deps are already in the `dev-atiis` env (`requirements.txt` pins them; nothing
new to install). For live runs, add your key:

```bash
cp experiment/.env.example experiment/.env   # then edit OPENROUTER_API_KEY
```

## Run (from the `experiment/` directory)

```bash
python -m sweeps.sweep1_p0 --dry        # render prompts + oracle, no API key
python -m sweeps.sweep1_p0 --limit 5    # quick live smoke test (caps API calls)
python -m sweeps.sweep1_p0              # full sweep
```

Then open `analysis/sweep1_p0.ipynb`.

## Design notes baked into the code

- **No numbers in prompts.** Subjective parameters (belief, cost, lobbying
  effect) are ordinal ids → natural-language wordings. The probability/cost
  numbers exist only in `engine/oracle.py`, flagged as a *reference* for the
  formal calculation — never as a claim that a wording equals a value. That
  mapping is what the experiment tests (`inferred_probability`).
- **Two oracle comparisons per call.** `oracle_at_reference` (our nominal
  mapping) and `oracle_at_inferred` (committee.py fed the model's own
  `inferred_probability`, assumption-free).
- **All run knobs in one file** (`sweeps/sweep1_p0.py`). Adding a robustness
  axis later (e.g. repeat over `vote` or `c_sw`) is a config change, not an
  engine change (`SECONDARY_AXIS`).
- **Adding a scenario** = a new `prompts/sXX/scenario.py` exposing
  `TEMPLATE`, `PHRASINGS`, `render`. The engine is content-blind.
