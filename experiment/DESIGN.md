# Experimental Design

## Question

When an LLM reasons about blame in a collective decision, is it sensitive to the
counterfactual structure of the situation, or does it classify agents by their
surface moral action and stop there?

"Counterfactual structure" means who was pivotal, what alternative actions were
available, how costly those actions were, and how much they would have changed
the outcome. That is what the formal framework in `framework/committee.py`
computes. "Surface moral action" means the folk rule: you voted no, you are to
blame; you voted yes, you are not.

The finding is not binary. The LLM will not be purely one or the other. The
contribution is the profile: the model may track some structural features and
ignore others, and that profile is informative about what LLM moral cognition
looks like in collective settings.

| Feature | Counterfactual reasoning | Surface reasoning |
|---|---|---|
| Belief (p0) | Modulates blame non-monotonically by pivotality | Ignores beliefs entirely |
| Own vote | Nonzero residual blame for the yes-voter (could have lobbied) | Zero blame for the yes-voter |
| Cost of switching | Discounts blame as cost rises | Same blame regardless of cost |
| Stakes (balance N) | Flattens the cost discount as stakes rise | Insensitive to stakes |
| Pressure effectiveness (alpha) | Tracks marginal contribution across coalition actions | Ignores the lobbying channel |

## Scope

The experiment is a single sweep over the focal agent's belief, p0. That sweep
is the headline result. The other parameters (own vote, pressure effectiveness
alpha, switching cost, and stakes) are not run as full sweeps. They are run as
one-variable-at-a-time (OFAT) validation arms on the p0 sweep: the whole p0 curve
is re-run with exactly one of these variables changed, and we check that the
LLM's curve shifts in the same direction the formal oracle's curve shifts. This
is a lighter design than six independent sweeps, and it directly answers a
narrower but well-posed question: does the model behave, across these variables,
as if it were reasoning with the framework?

Full independent sweeps over these variables, additional scenario skins, and
other parameters are described under Deferred Work at the end.

## The Formal Oracle

`framework/committee.py` implements the Friedenberg and Halpern Shapley-blame
framework (a committee of n agents, a threshold vote, a binary outcome). It is
the ground-truth oracle. `engine/oracle.py` is the only place in the experiment
where ordinal ids become numbers. The reference tables below are a modelling
assumption used to compute the oracle. They are not a claim that the phrasing
"low" equals p0 = 0.10. Whether the model reads a phrasing as the intended level
is part of what the experiment tests.

Reference values (oracle only, isolated in `engine/oracle.py`):

| Parameter | Ordinal id and reference value |
|---|---|
| p0 (belief) | very_low 0.10, low 0.20, somewhat_low 0.35, even 0.50, somewhat_high 0.60, high 0.80, very_high 0.90 |
| c_sw (switch cost) | trivial 200, minor 500, significant 2000, severe 3000 |
| alpha (pressure effect) | negligible 0.01, slim 0.03, modest 0.05, strong 0.10 |
| Stakes to N (balance) | low 2500, default 5000, high 12000 |

The pressure cost is held at 100. The balance parameter N must exceed the largest
switch cost. Stakes is the natural-language proxy for N: high N means costs are
small next to what is at stake, low N means they weigh heavily.

The framework natively clamps coalition pressure (the boost n times alpha is
capped so a probability never exceeds 1), so an inferred alpha can be passed
straight through without extra handling.

## Scenario Skins

All prompts follow a committee skeleton that is structurally isomorphic to the
formal example but differs in surface content. Running more than one skin checks
whether findings generalize across narratives.

- Scenario A (implemented): a hospital board of seven attending physicians must
  authorize a treatment. Authorization needs at least four sign-offs. The board
  fell short and the treatment was not administered. The reader evaluates the
  blame of one physician.
- Scenario B and C (deferred): additional skins (for example a grant committee)
  in a different surface domain, exposing the same interface.

## Number-Free Prompts

No probabilities or costs as numbers ever enter a prompt. Subjective parameters
(belief, cost, pressure effectiveness) appear only as natural-language wordings
keyed by ordinal id. The only genuine numbers in a prompt are objective scenario
facts (committee size, vote threshold).

### Stimulus sampling (phrasings)

For each level of the swept variable, three independent phrasings convey the same
intended value through different words. If the LLM responds consistently across
phrasings, the signal comes from the parameter, not the wording. If it does not,
that inconsistency is itself a finding. The three phrasings of the swept variable
are run exhaustively (each phrasing gets the full repetition count), which gives
a balanced estimate of phrasing variance. Held variables, including the one
changed in a validation arm, use a single fixed wording so that an arm differs
from baseline by exactly one wording and any curve shift is attributable to that
one variable.

### Per-call inference and unit mappings

Every call asks the model to report its own reading of the subjective parameters
present in the prompt, on a 0 to 100 integer scale. This lets the oracle be
recomputed with the model's own perceived values, an assumption-free comparison
that does not depend on the reference tables.

- inferred_probability: the probability the focal agent assigned to enough
  colleagues approving. Mapped to p0 as x divided by 100.
- inferred_alpha: the percent chance that lobbying one colleague changes that
  colleague's position. Mapped to alpha as x divided by 100. The framework's
  native clamp keeps the coalition boost valid.
- inferred_cost: present only for a no-voter (a yes-voter faced no switch
  decision). It is the switch cost expressed as a percentage of how harmful the
  outcome is, which is exactly the ratio c_sw over N. The discount term in the
  blame formula, one minus c_sw over N, is then one minus x over 100. N stays at
  its reference value; only the ratio is used.

Each call therefore yields two oracle comparisons: oracle_at_reference (the
nominal mapping) and oracle_at_inferred (the framework fed the model's own
inferred p0, alpha, and cost).

## The Sweep: Belief (p0)

The focal agent voted no. We vary how confident the agent was that the others
would approve, holding switching cost at significant, pressure effectiveness at
modest, stakes at default, and the threshold at four of seven.

Levels: very_low, low, somewhat_low, even, somewhat_high, high, very_high.

What the framework predicts: blame is non-monotonic in p0. It peaks at a moderate
belief and falls toward zero at both extremes. When the outcome feels inevitable
either way, no single action is pivotal, so the marginal contribution goes to
zero.

Null hypothesis: the LLM's blame for the focal agent does not vary systematically
with the described belief, or varies only monotonically.

Finding paths:

- Non-monotonic peak reproduced: the model has internalized pivotality. The
  strongest and least expected result.
- Monotonic increase (more optimistic, more blame): a "you should have known
  better" heuristic. Formally wrong, since at high p0 the proposal nearly passes
  without the focal agent, so their marginal impact is small. Diagnosis:
  outcome-expectation bias.
- Monotonic decrease (more pessimistic, more blame): an effort-opportunity
  intuition. Formally wrong for the opposite reason, since at low p0 no coalition
  action moves the outcome.
- Flat blame: the model treats the vote as the sole determinant and ignores
  epistemic context. Diagnosis: act-based reasoning with no sensitivity to
  counterfactual impact.

## Validation Arms (OFAT)

Each arm re-runs the whole p0 curve with one held variable changed. The check is
whether the LLM curve shifts the way the oracle curve shifts. The baseline arm is
the headline p0 run above.

### Own vote (vote_yes)

Change: the focal agent voted yes instead of no. The cost sentence (and the
inferred_cost field) is removed, since a yes-voter faced no switch decision.

What the framework predicts: the yes-voter still carries nonzero blame, because
they could have applied social pressure to others, but less than the no-voter. In
the formal example the ratio is roughly three to one.

What we test: that yes-voter blame is greater than zero (against the folk rule
that voting yes is fully exonerating) and that no-voter blame exceeds yes-voter
blame, with a ratio in the right ballpark.

### Pressure effectiveness (alpha_negligible, alpha_strong)

Change: alpha is set to negligible or to strong instead of modest.

What the framework predicts: alpha moves the location of the peak of the blame
versus p0 curve, because more effective lobbying changes how pivotal the focal
agent is across available coalition actions. The non-monotonic hump survives; its
peak moves.

What we test: that the LLM peak location shifts in the same direction as the
oracle peak location, and that the overall blame distribution shifts relative to
baseline.

### Switching cost and stakes (cost_trivial, stakes_high)

Change: either the switch cost is set to trivial instead of significant, or the
stakes are set to high instead of default (which raises the balance parameter N).

What the framework predicts: lower switch cost gives higher blame (a smaller cost
discount). Higher stakes (higher N) flatten the cost discount, so blame stays
higher even for costly actions.

What we test: that blame shifts relative to baseline in the predicted direction,
and that the slope of blame against the model's own inferred cost has the
predicted sign (the assumption-free cost-discount check).

## Running Logic

One arm is one run. `engine/runner.py` executes a single arm of the sweep and
writes a self-describing directory:

```
results/<sweep>/<scenario>/<model>/<arm>/<UTC-stamp>/
    manifest.json   full run config plus the oracle constants in force
    rows.jsonl      full per-call log
    rows.csv        tidy columns for analysis
```

`manifest.json` snapshots everything needed to reproduce and to recompute the
oracle: model, temperature, repetitions, seed, levels, arm name and overrides,
held parameters, the wording policy, and the oracle block (the balance parameter,
the pressure cost, and the reference tables for p0, cost, alpha, and stakes to N),
plus a code version and timestamps. Provenance lives in data, not in filenames.

`run.py` is the driver. It expands a set of (model, scenario, arm) combinations
and calls the runner once per combination, de-duplicating the shared baseline run:

- Headline coverage: the baseline arm across all models and all scenario skins.
- Validation coverage: all arms across all models, on Scenario A only.

This keeps the validation cost bounded while still showing that the effects are
not specific to one model.

## Statistical Analysis

The analysis (`analysis/analysis.ipynb`, fed by `analysis/loader.py`, which globs
every manifest into one tidy table) reports shape agreement separately from
magnitude agreement, and uses rank-based and paired tests appropriate to a
bounded, skewed blame score.

Headline (baseline arm, all models and scenarios):

- Rank agreement: Spearman correlation between the LLM blame and the oracle, with
  a percentile bootstrap confidence interval, computed against both
  oracle_at_reference and oracle_at_inferred.
- Non-monotonicity: a quadratic fit of blame on the level rank, testing the
  quadratic term, plus a comparison of the fitted LLM peak rank to the oracle
  peak rank. A bare monotone correlation would miss the predicted hump.
- Curves: blame versus p0 with the oracle overlaid, one panel per model.
- Variance decomposition: the share of blame variance explained by the parameter
  versus the phrasing within a level (an ICC-style summary of parameter signal
  against wording noise). A formal mixed model is available as an optional cell.

Validation (Scenario A, per arm):

- vote_yes: Wilcoxon signed-rank pairing no against yes by level, phrasing, and
  repetition; McNemar on the binary blame-equals-zero outcome for the yes-voter;
  the no over yes blame ratio against the oracle ratio.
- alpha arms: the LLM peak shift against the oracle peak shift; Mann-Whitney
  against baseline.
- cost and stakes arms: Mann-Whitney against baseline; the slope of blame against
  the model's inferred cost.
- oracle_at_inferred agreement (Spearman) on every arm.

Multiple comparisons are controlled with a Benjamini-Hochberg correction across
the grid of tests. Tables are written to `analysis/tables/` as CSV and LaTeX and
figures to `analysis/figures/` for direct embedding in the report.

## Limitations

- Single scenario for validation. The validation arms run on Scenario A only.
  Wording and narrative effects on the arm results are therefore not controlled
  across skins.
- OFAT, not factorial. Each arm changes one variable around a single baseline.
  Interactions between variables are not measured.
- Inferred-value elicitation. Asking the model for its own reading of alpha and
  cost adds a self-report channel that may itself be noisy or miscalibrated; the
  reference oracle is reported alongside the inferred oracle precisely so the two
  can be compared.
- Coalition amplification is conveyed qualitatively. The prompt states the
  direction (more colleagues advocating improves the odds) but cannot carry the
  exact functional form of the coalition boost. Report shape and rank agreement
  as primary; treat peak-location agreement as approximate.
- Language. All vignettes are in English.

## Deferred Work

The following were considered and are out of scope for the current re-scope. They
remain the natural extensions if the p0 results show clear structure.

- Full independent sweeps over own vote, switching cost crossed with stakes,
  pressure effectiveness, voting threshold, and group size, each with full
  stimulus sampling and a mixed-effects treatment of phrasing and scenario.
- The cost of collective coordination (the pressure cost) as a distinct sweep,
  testing whether cost sensitivity extends from individual sacrifice to
  coordination overhead.
- Additional scenario skins (B and C) for the validation arms, to control wording
  and narrative effects.
- Cross-linguistic replication.
