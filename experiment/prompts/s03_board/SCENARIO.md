# Scenario s03 — Corporate Board Capital Decision

**Domain:** Corporate finance (cold). **Source of truth:** `scenario.py` (this card is documentation).

A board of *n* directors must authorize a major financial commitment;
authorization needs at least `pass_threshold` votes in favor. The board falls
short, the commitment is not authorized, and the evaluator judges how
blameworthy the focal director (**Director Castellan**) is. Structurally
isomorphic to the Friedenberg-Halpern committee example and to s01.

## Role in the design (cold-affect contrast)

This skin is deliberately low-affect: there is no human victim, and the only
consequence of inaction is financial (a forgone gain or loss to the firm). It
therefore doubles as a stakes/affect contrast to the weighty s01/s02 skins. If
the p0 curve is stable here too, structure-tracking is robust to narrative AND
to affective load; if it flattens or shifts, affect (not structure) is moving
the blame judgment. See `../s02_grant/SCENARIO.md` for the matched-stakes
narrative-invariance skin.

## Number-isolation principle

No probability or cost appears as a number in any prompt. Subjective parameters
are expressed only as natural-language wordings keyed by **ordinal id**. The
numeric values used to compute the formal oracle live in `engine/oracle.py`,
flagged as a modelling reference, not a claim that a wording equals a value. The
model is asked to report `inferred_probability` (and `inferred_alpha`, plus
`inferred_cost` for a no-voter), which is precisely what lets us test that
mapping rather than assume it. The only genuine numbers in a prompt are
objective facts: board size and vote threshold.

## Mapping from s01 (only the domain verb changes)

| s01 (health) | s03 (board) |
|---|---|
| board of physicians | board of directors |
| sign the authorization | vote in favor of the commitment |
| treatment not administered | commitment not authorized |
| Dr. Aris | Director Castellan |

The `c_sw` and `alpha` wordings are domain-neutral and identical to s01; the
`p0`, vote, coalition, and stakes wordings are the s01 wordings with the
corporate verb substituted, to hold everything but the narrative (and its
affective load) constant. The `inferred_cost` question references "how costly
the commitment not being authorized is" rather than "how harmful", matching the
cold framing.

## Ordinal levels

Same ids and oracle reference values as s01 (see `../s01_health/SCENARIO.md`):
`p0` very_low..very_high, `c_sw` trivial..severe, `alpha` negligible..strong,
`vote` no/yes, `stakes` default/low/high. Each subjective level has **3
independent wordings**.

## Model output contract

```json
{
  "reasoning": "<rationale>",
  "blameworthiness": 0-100,
  "inferred_probability": 0-100,
  "inferred_alpha": 0-100,
  "inferred_cost": 0-100      // present only for a no-voter
}
```
