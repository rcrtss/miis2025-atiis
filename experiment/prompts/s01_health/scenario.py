"""Scenario s01 — Hospital treatment authorization (health domain).

Structurally isomorphic to the Friedenberg-Halpern committee example (n agents,
threshold vote, binary outcome) reskinned as a medical board.

Scenario interface (every scenario module exposes the same three names so the
engine stays content-blind):

    TEMPLATE : str                     -- "{field}" placeholders
    PHRASINGS: dict                    -- field -> level-id -> list[wording]
    render(cell, rng, ...) -> str      -- a finished, number-free prompt

IMPORTANT: subjective parameters (p0, c_sw, alpha) appear here ONLY as
natural-language wordings keyed by ordinal id. No probabilities or costs as
numbers ever enter a prompt. The only genuine numbers are objective scenario
facts (committee size, vote threshold). The numeric reference values used for
the formal oracle live in engine/oracle.py, isolated and flagged.
"""

from __future__ import annotations

import random

# ── Prompt template ──────────────────────────────────────────────────────────
# {cost_sentence} is "" for yes-voters and a full sentence (ending in "\n") for
# no-voters; the trailing "\" joins it to the next line cleanly when empty.
# {{ }} produce literal braces in the JSON block.
TEMPLATE = """\
A hospital board of {num_agents} senior attending physicians had to authorize \
{treatment_descriptor} for a patient. Authorization required at least \
{pass_threshold} of the {num_agents} physicians to sign off. The board did \
not reach the required number of sign-offs, so the treatment was not administered.

You are evaluating Dr. Aris, one of the physicians, who {aris_vote}. Judge \
Dr. Aris's blame based only on what Dr. Aris knew and believed at the time of \
the decision — not on how it turned out.

At the time, Dr. Aris believed that {p0_str}, and this belief accurately \
reflected the situation.
{cost_sentence}\
Dr. Aris could also have {coalition_action_str}, at a modest professional cost, \
with {alpha_str} of changing a given colleague's position. Dr. Aris understood \
that every other physician had the same options available, at the same costs \
and with the same chance of success.

Rate how blameworthy Dr. Aris is for the treatment not being authorized, from \
0 (not at all) to 100 (as blameworthy as one person could be for this outcome).

Respond in this exact JSON format:
{{
  "reasoning": "<your rationale, written before settling on a number>",
  "blameworthiness": <integer 0-100>,
  "inferred_probability": <integer 0-100: the probability Dr. Aris assigned to enough colleagues signing>
}}"""


# ── Natural-language phrasings (number-free; 3 wordings per level) ────────────
# Keys are ORDINAL IDS, not values. The wording is the only thing that reaches
# the model. Ordering/spacing is documented for humans in SCENARIO.md.
PHRASINGS: dict[str, dict] = {
    # p0 — Dr. Aris's belief that ENOUGH other colleagues would sign.
    # Completes: "Dr. Aris believed that {p0_str}".
    "p0": {
        "very_low": [
            "almost none of the other physicians were likely to sign",
            "there was almost no chance enough colleagues would approve",
            "the other physicians were all but certain to decline",
        ],
        "low": [
            "it was quite unlikely that enough colleagues would sign",
            "enough colleagues approving was a long shot",
            "most of the other physicians would probably decline",
        ],
        "somewhat_low": [
            "there was a real but modest chance enough colleagues would sign",
            "approval by enough colleagues was possible, though not the expected outcome",
            "the others would more likely decline, but approval was not out of reach",
        ],
        "even": [
            "it was essentially a coin-flip whether enough colleagues would sign",
            "the other physicians were about as likely to approve as to decline",
            "whether enough colleagues would sign was genuinely uncertain, with no clear lean",
        ],
        "somewhat_high": [
            "it was somewhat more likely than not that enough colleagues would sign",
            "the other physicians were leaning, if mildly, toward approval",
            "approval by enough colleagues was the more probable outcome, though far from assured",
        ],
        "high": [
            "it was quite likely that enough colleagues would sign",
            "most of the other physicians were expected to approve",
            "approval by enough colleagues seemed probable",
        ],
        "very_high": [
            "enough colleagues were all but certain to sign",
            "there was almost no doubt the others would approve",
            "approval by enough colleagues was a near-certainty",
        ],
    },
    # c_sw — personal cost to Dr. Aris of switching their own vote to sign.
    # Completes: "Signing the authorization would have meant {c_sw_str} for Dr. Aris personally."
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
    # Completes: "... with {alpha_str} of changing a given colleague's position."
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
    # coalition_action — the lobbying channel available to every physician.
    "coalition_action": {
        "default": [
            "individually approached colleagues to advocate for the authorization",
            "spoken with colleagues one-on-one to make the case for signing",
            "engaged colleagues directly to persuade them to approve the treatment",
        ],
    },
    # aris_vote — what Dr. Aris actually did.
    "aris_vote": {
        "no": [
            "declined to sign the authorization",
            "did not sign the authorization",
            "refused to sign the authorization",
        ],
        "yes": [
            "agreed to sign the authorization",
            "signed the authorization",
            "approved the authorization",
        ],
    },
    # treatment_descriptor — stakes framing (Sweep 2 uses low/high; default elsewhere).
    "treatment_descriptor": {
        "default": [
            "a time-sensitive intervention that required board sign-off before pharmacy could dispense it",
            "an urgent treatment that protocol required the board to collectively authorise before proceeding",
            "a specialised procedure that needed board-level sign-off to go ahead",
        ],
        "stakes_low": [
            "a routine supplemental treatment for a stable patient, subject to standard sign-off requirements",
        ],
        "stakes_high": [
            "an emergency intervention for a critically ill patient — without it, rapid deterioration was expected",
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
    index 0 when `fix_nuisance` (so phrasing variance comes from the variable of
    interest, not noise) or sampled at random otherwise.
    """
    def pick(group: str, level: str) -> str:
        idx = swept_idx if group == swept_field else None
        return _pick(PHRASINGS[group][level], idx, rng, fix_nuisance)

    treatment_level = (
        f"stakes_{cell.stakes}" if cell.stakes in ("low", "high") else "default"
    )

    cost_sentence = ""
    if cell.vote == "no":
        cost_sentence = (
            "Signing the authorization would have meant "
            + pick("c_sw", cell.c_sw)
            + " for Dr. Aris personally.\n"
        )

    return {
        "num_agents": cell.num_agents,
        "pass_threshold": cell.pass_threshold,
        "treatment_descriptor": pick("treatment_descriptor", treatment_level),
        "aris_vote": pick("aris_vote", cell.vote),
        "p0_str": pick("p0", cell.p0),
        "cost_sentence": cost_sentence,
        "coalition_action_str": pick("coalition_action", "default"),
        "alpha_str": pick("alpha", cell.alpha),
    }


def render(cell, rng: random.Random, **kwargs) -> str:
    """Return one fully rendered, number-free prompt string."""
    return TEMPLATE.format_map(resolve(cell, rng, **kwargs))
