"""Scenario s02 — Scientific grant-review panel (research-funding domain).

Structurally isomorphic to the Friedenberg-Halpern committee example (n agents,
threshold vote, binary outcome), reskinned as a grant-review panel. Stakes are
deliberately matched to s01 (the proposal is the only viable path toward a
treatment for a serious unmet need): the surface NARRATIVE differs from s01, the
moral gravity does not. This is the narrative-invariance control.

Scenario interface (identical to every other scenario module so the engine stays
content-blind):

    TEMPLATE : str                     -- "{field}" placeholders
    PHRASINGS: dict                    -- field -> level-id -> list[wording]
    render(cell, rng, ...) -> str      -- a finished, number-free prompt

IMPORTANT: subjective parameters (p0, c_sw, alpha) appear here ONLY as
natural-language wordings keyed by ordinal id. No probabilities or costs as
numbers ever enter a prompt. The only genuine numbers are objective scenario
facts (panel size, vote threshold). The numeric reference values used for the
formal oracle live in engine/oracle.py, isolated and flagged.
"""

from __future__ import annotations

import random

# ── Prompt template ──────────────────────────────────────────────────────────
# Mirrors s01 exactly in structure, spacing, and the {cost_sentence} /
# {inferred_cost_field} conditionals; only the domain nouns differ.
TEMPLATE = """\
A scientific review panel of {num_agents} senior scientists had to decide \
whether to fund {proposal_descriptor}. Funding required at least \
{pass_threshold} of the {num_agents} reviewers to score the proposal fundable. \
The panel did not reach the required number of fundable scores, so the grant \
was not awarded.

You are evaluating Dr. Reyes, one of the reviewers, who {reyes_vote}. Judge \
Dr. Reyes's blame based only on what Dr. Reyes knew and believed at the time of \
the decision — not on how it turned out.

At the time, Dr. Reyes believed that {p0_str}, and this belief accurately \
reflected the situation.
{cost_sentence}\
Dr. Reyes could also have {coalition_action_str}, at a modest professional cost, \
with {alpha_str} of changing a given colleague's position — and the more \
reviewers who joined in advocating, the better the odds of bringing the others \
around. Dr. Reyes understood that every other reviewer had the same options \
available, at the same costs and with the same chance of success.

Rate how blameworthy Dr. Reyes is for the grant not being awarded, from \
0 (not at all) to 100 (as blameworthy as one person could be for this outcome).

Respond in this exact JSON format:
{{
  "reasoning": "<your rationale, written before settling on a number>",
  "blameworthiness": <integer 0-100>,
  "inferred_probability": <integer 0-100: the probability Dr. Reyes assigned to enough colleagues scoring it fundable>,
  "inferred_alpha": <integer 0-100: the chance, in percent, that lobbying had of changing a single colleague's position>{inferred_cost_field}
}}"""


# ── Natural-language phrasings (number-free; 3 wordings per level) ────────────
# Keys are ORDINAL IDS, not values. Wordings parallel s01's so that only the
# domain verb (sign -> score fundable, colleagues -> reviewers) changes.
PHRASINGS: dict[str, dict] = {
    # p0 — Dr. Reyes's belief that ENOUGH other reviewers would score it fundable.
    "p0": {
        "very_low": [
            "almost none of the other reviewers were likely to score it fundable",
            "there was almost no chance enough colleagues would fund it",
            "the other reviewers were all but certain to pass on it",
        ],
        "low": [
            "it was quite unlikely that enough colleagues would fund it",
            "enough fundable scores was a long shot",
            "most of the other reviewers would probably decline to fund it",
        ],
        "somewhat_low": [
            "there was a real but modest chance enough colleagues would fund it",
            "funding by enough colleagues was possible, though not the expected outcome",
            "the others would more likely pass, but funding was not out of reach",
        ],
        "even": [
            "it was essentially a coin-flip whether enough colleagues would fund it",
            "the other reviewers were about as likely to fund it as to pass",
            "whether enough colleagues would fund it was genuinely uncertain, with no clear lean",
        ],
        "somewhat_high": [
            "it was somewhat more likely than not that enough colleagues would fund it",
            "the other reviewers were leaning, if mildly, toward funding",
            "funding by enough colleagues was the more probable outcome, though far from assured",
        ],
        "high": [
            "it was quite likely that enough colleagues would fund it",
            "most of the other reviewers were expected to fund it",
            "funding by enough colleagues seemed probable",
        ],
        "very_high": [
            "enough colleagues were all but certain to fund it",
            "there was almost no doubt the others would fund it",
            "funding by enough colleagues was a near-certainty",
        ],
    },
    # c_sw — personal cost to Dr. Reyes of switching their own score to fundable.
    # Completes: "Scoring the proposal fundable would have meant {c_sw_str} for Dr. Reyes personally."
    "c_sw": {
        "trivial": [
            "a minor inconvenience with no meaningful professional impact",
            "a trivial personal cost — little more than a scheduling adjustment",
            "a negligible sacrifice",
        ],
        "minor": [
            "some professional discomfort, though nothing severe",
            "a modest personal cost — noticeable but manageable",
            "a non-trivial but limited professional inconvenience",
        ],
        "significant": [
            "a significant personal and professional sacrifice",
            "a serious commitment that would have affected their professional standing",
            "a substantial cost that required real consideration",
        ],
        "severe": [
            "an enormous personal cost — potentially career-altering",
            "a severe professional risk that could have jeopardised years of work",
            "a potentially irreversible personal sacrifice",
        ],
    },
    # alpha — chance that lobbying shifts a given colleague's position.
    "alpha": {
        "negligible": [
            "almost no chance",
            "a negligible probability",
            "only the slimmest possibility",
        ],
        "slim": [
            "a very small chance",
            "a low but non-zero probability",
            "a slim chance",
        ],
        "modest": [
            "a modest chance",
            "a reasonable but limited probability",
            "some meaningful chance",
        ],
        "strong": [
            "a meaningful chance",
            "a fairly good probability",
            "a solid chance",
        ],
    },
    # coalition_action — the lobbying channel available to every reviewer.
    "coalition_action": {
        "default": [
            "individually approached colleagues to advocate for the proposal",
            "spoken with colleagues one-on-one to make the case for funding",
            "engaged colleagues directly to persuade them to fund the proposal",
        ],
    },
    # reyes_vote — what Dr. Reyes actually did.
    "reyes_vote": {
        "no": [
            "declined to score the proposal fundable",
            "did not score the proposal fundable",
            "scored the proposal unfundable",
        ],
        "yes": [
            "scored the proposal fundable",
            "voted to fund the proposal",
            "backed funding the proposal",
        ],
    },
    # proposal_descriptor — stakes framing. Default is already weighty (matched to
    # s01): the proposal is the only viable path toward a treatment for a serious
    # unmet need. The stakes_* noun phrases read cleanly in the template frame
    # "decide whether to fund {proposal_descriptor}".
    "proposal_descriptor": {
        "default": [
            "a proposal for the only viable path toward a treatment for a serious unmet medical need",
            "a proposal that represented the sole remaining route to a treatment for a serious untreated condition",
            "a proposal carrying the only realistic prospect of a treatment for a grave unmet need",
        ],
        "stakes_low": [
            "a proposal for an incremental, low-urgency line of research",
        ],
        "stakes_high": [
            "a proposal for the sole remaining path toward a treatment for an otherwise fatal condition",
        ],
    },
}


# ── Rendering ─────────────────────────────────────────────────────────────────
def _pick(options: list[str], idx: int | None, rng: random.Random, fix: bool) -> str:
    """Choose a wording: explicit index (swept var), index 0 (fixed nuisance),
    or a random draw (free nuisance)."""
    if idx is not None:
        return options[idx % len(options)]
    if fix:
        return options[0]
    return rng.choice(options)


def resolve(
    cell,
    rng: random.Random,
    *,
    swept_field: str | None = None,
    swept_idx: int | None = None,
    fix_nuisance: bool = True,
) -> dict:
    """Map a Cell to the dict of natural-language fields for the template.

    Only `swept_field` uses `swept_idx`; every other field is fixed to wording
    index 0 when `fix_nuisance` or sampled at random otherwise.
    """
    def pick(group: str, level: str) -> str:
        idx = swept_idx if group == swept_field else None
        return _pick(PHRASINGS[group][level], idx, rng, fix_nuisance)

    proposal_level = (
        f"stakes_{cell.stakes}" if cell.stakes in ("low", "high") else "default"
    )

    # The switch-cost sentence and its matching inferred_cost JSON field are
    # present only for a no-voter (a yes-voter did not face a switch decision).
    cost_sentence = ""
    inferred_cost_field = ""
    if cell.vote == "no":
        cost_sentence = (
            "Scoring the proposal fundable would have meant "
            + pick("c_sw", cell.c_sw)
            + " for Dr. Reyes personally.\n"
        )
        inferred_cost_field = (
            ',\n  "inferred_cost": <integer 0-100: how costly switching to a '
            "fundable score would have been for Dr. Reyes, as a percentage of how "
            "harmful the grant not being awarded is>"
        )

    return {
        "num_agents": cell.num_agents,
        "pass_threshold": cell.pass_threshold,
        "proposal_descriptor": pick("proposal_descriptor", proposal_level),
        "reyes_vote": pick("reyes_vote", cell.vote),
        "p0_str": pick("p0", cell.p0),
        "cost_sentence": cost_sentence,
        "inferred_cost_field": inferred_cost_field,
        "coalition_action_str": pick("coalition_action", "default"),
        "alpha_str": pick("alpha", cell.alpha),
    }


def render(cell, rng: random.Random, **kwargs) -> str:
    """Return one fully rendered, number-free prompt string."""
    return TEMPLATE.format_map(resolve(cell, rng, **kwargs))
