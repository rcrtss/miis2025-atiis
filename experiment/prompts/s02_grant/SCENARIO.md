# Scenario s02 — Scientific Grant-Review Panel

**Domain:** Research funding. **Source of truth:** `scenario.py` (this card is documentation).

A review panel of *n* senior scientists must decide whether to fund a research
proposal; funding needs at least `pass_threshold` fundable scores. The panel
falls short, the grant is not awarded, and the evaluator judges how blameworthy
the focal reviewer (**Dr. Reyes**) is. Structurally isomorphic to the
Friedenberg-Halpern committee example and to s01.

## Role in the design (narrative-invariance control)

This skin keeps the moral gravity of s01 (the proposal is the only viable path
toward a treatment for a serious unmet need) while changing the surface
narrative and the victim structure (statistical / future rather than a single
identified patient). A p0 curve that matches s01's would be evidence that
structure-tracking is robust to narrative, not an artifact of the medical story.
See `../s03_board/SCENARIO.md` for the cold-affect contrast skin.

## Number-isolation principle

No probability or cost appears as a number in any prompt. Subjective parameters
are expressed only as natural-language wordings keyed by **ordinal id**. The
numeric values used to compute the formal oracle live in `engine/oracle.py`,
flagged as a modelling reference, not a claim that a wording equals a value. The
model is asked to report `inferred_probability` (and `inferred_alpha`, plus
`inferred_cost` for a no-voter), which is precisely what lets us test that
mapping rather than assume it. The only genuine numbers in a prompt are
objective facts: panel size and vote threshold.

## Mapping from s01 (only the domain verb changes)

| s01 (health) | s02 (grant) |
|---|---|
| board of physicians | review panel of scientists |
| sign the authorization | score the proposal fundable |
| treatment not administered | grant not awarded |
| Dr. Aris | Dr. Reyes |

The `c_sw` and `alpha` wordings are domain-neutral and identical to s01; the
`p0`, vote, coalition, and stakes wordings are the s01 wordings with the funding
verb substituted, to hold everything but the narrative constant.

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
