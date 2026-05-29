# Scenario s01 — Hospital Treatment Authorization

**Domain:** Healthcare. **Source of truth:** `scenario.py` (this card is documentation).

A hospital board of *n* attending physicians must authorize a treatment;
authorization needs at least `pass_threshold` sign-offs. The board falls short,
the treatment is withheld, and the evaluator judges how blameworthy the focal
physician (**Dr. Aris**) is. Structurally isomorphic to the Friedenberg–Halpern
committee example.

## Number-isolation principle

No probability or cost appears as a number in any prompt. Subjective parameters
are expressed only as natural-language wordings keyed by **ordinal id**. The
numeric values used to compute the formal oracle live in `engine/oracle.py`,
flagged as a modelling reference — *not* a claim that a wording equals a value.
The model is asked to report `inferred_probability`, which is precisely what
lets us test that mapping rather than assume it.

The only genuine numbers in a prompt are objective facts: committee size and
vote threshold ("at least 4 of 7 physicians").

## Rendered template

```
A hospital board of {num_agents} senior attending physicians had to authorize
{treatment_descriptor} for a patient. Authorization required at least
{pass_threshold} of the {num_agents} physicians to sign off. The board did not
reach the required number of sign-offs, so the treatment was not administered.

You are evaluating Dr. Aris, one of the physicians, who {aris_vote}. Judge
Dr. Aris's blame based only on what Dr. Aris knew and believed at the time of
the decision — not on how it turned out.

At the time, Dr. Aris believed that {p0_str}, and this belief accurately
reflected the situation.
{cost_sentence}Dr. Aris could also have {coalition_action_str}, at a modest
professional cost, with {alpha_str} of changing a given colleague's position.
Dr. Aris understood that every other physician had the same options available,
at the same costs and with the same chance of success.

Rate how blameworthy Dr. Aris is ... (JSON response requested)
```

`{cost_sentence}` is present only for no-voters.

## Ordinal levels

| Field | Ordinal ids (low → high) | Oracle reference (isolated) |
|-------|--------------------------|------------------------------|
| `p0` (belief others sign) | very_low, low, somewhat_low, even, somewhat_high, high, very_high | 0.10 / 0.20 / 0.35 / 0.50 / 0.60 / 0.80 / 0.90 |
| `c_sw` (switch cost) | trivial, minor, significant, severe | 200 / 500 / 2000 / 3000 |
| `alpha` (lobbying effect) | negligible, slim, modest, strong | 0.01 / 0.03 / 0.05 / 0.10 |
| `vote` | no, yes | focal prob 0.0 / 1.0 |
| `stakes` | default, low, high | (Sweep 2) |

Each subjective level has **3 independent wordings**; the sweep picks among them
to separate the parameter signal from the specific phrasing.

## Model output contract

```json
{
  "reasoning": "<rationale>",
  "blameworthiness": 0-100,
  "inferred_probability": 0-100
}
```
