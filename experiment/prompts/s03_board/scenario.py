"""Scenario s03 — Corporate board capital decision (cold financial domain).

Structurally isomorphic to the Friedenberg-Halpern committee example (n agents,
threshold vote, binary outcome), reskinned as a corporate board authorizing a
major financial commitment. Stakes are deliberately COLD: no human victim, the
only consequence of inaction is financial (a forgone gain / loss to the firm).
This skin doubles as a low-affect contrast to s01/s02: if the p0 curve is stable
here too, structure-tracking is robust to narrative AND to affective load.

Scenario interface (identical to every other scenario module so the engine stays
content-blind):

    TEMPLATE : str                     -- "{field}" placeholders
    PHRASINGS: dict                    -- field -> level-id -> list[wording]
    render(cell, rng, ...) -> str      -- a finished, number-free prompt

IMPORTANT: subjective parameters (p0, c_sw, alpha) appear here ONLY as
natural-language wordings keyed by ordinal id. No probabilities or costs as
numbers ever enter a prompt. The only genuine numbers are objective scenario
facts (board size, vote threshold). The numeric reference values used for the
formal oracle live in engine/oracle.py, isolated and flagged.
"""

from __future__ import annotations

import random

# ── Prompt template ──────────────────────────────────────────────────────────
# Mirrors s01 exactly in structure, spacing, and the {cost_sentence} /
# {inferred_cost_field} conditionals; only the domain nouns differ.
TEMPLATE = """\
A corporate board of {num_agents} directors had to authorize \
{deal_descriptor}. Authorization required at least {pass_threshold} of the \
{num_agents} directors to vote in favor. The board did not reach the required \
number of votes, so the commitment was not authorized.

You are evaluating Director Castellan, one of the board members, who \
{castellan_vote}. Judge Director Castellan's blame based only on what Director \
Castellan knew and believed at the time of the decision — not on how it turned \
out.

At the time, Director Castellan believed that {p0_str}, and this belief \
accurately reflected the situation.
{cost_sentence}\
Director Castellan could also have {coalition_action_str}, at a modest \
professional cost, with {alpha_str} of changing a given colleague's position — \
and the more directors who joined in advocating, the better the odds of \
bringing the others around. Director Castellan understood that every other \
director had the same options available, at the same costs and with the same \
chance of success.

Rate how blameworthy Director Castellan is for the commitment not being \
authorized, from 0 (not at all) to 100 (as blameworthy as one person could be \
for this outcome).

Respond in this exact JSON format:
{{
  "reasoning": "<your rationale, written before settling on a number>",
  "blameworthiness": <integer 0-100>,
  "inferred_probability": <integer 0-100: the probability Director Castellan assigned to enough colleagues voting in favor>,
  "inferred_alpha": <integer 0-100: the chance, in percent, that lobbying had of changing a single colleague's position>{inferred_cost_field}
}}"""


# ── Natural-language phrasings (number-free; 3 wordings per level) ────────────
# Keys are ORDINAL IDS, not values. Wordings parallel s01's so that only the
# domain verb (sign -> vote in favor, colleagues -> directors) changes.
PHRASINGS: dict[str, dict] = {
    # p0 — Castellan's belief that ENOUGH other directors would vote in favor.
    "p0": {
        "very_low": [
            "almost none of the other directors were likely to vote in favor",
            "there was almost no chance enough directors would approve it",
            "the other directors were all but certain to vote it down",
        ],
        "low": [
            "it was quite unlikely that enough directors would vote in favor",
            "enough votes in favor was a long shot",
            "most of the other directors would probably vote against it",
        ],
        "somewhat_low": [
            "there was a real but modest chance enough directors would vote in favor",
            "approval by enough directors was possible, though not the expected outcome",
            "the others would more likely vote against, but approval was not out of reach",
        ],
        "even": [
            "it was essentially a coin-flip whether enough directors would vote in favor",
            "the other directors were about as likely to approve as to reject",
            "whether enough directors would vote in favor was genuinely uncertain, with no clear lean",
        ],
        "somewhat_high": [
            "it was somewhat more likely than not that enough directors would vote in favor",
            "the other directors were leaning, if mildly, toward approval",
            "approval by enough directors was the more probable outcome, though far from assured",
        ],
        "high": [
            "it was quite likely that enough directors would vote in favor",
            "most of the other directors were expected to approve",
            "approval by enough directors seemed probable",
        ],
        "very_high": [
            "enough directors were all but certain to vote in favor",
            "there was almost no doubt the others would approve",
            "approval by enough directors was a near-certainty",
        ],
    },
    # c_sw — personal cost to Castellan of switching their own vote to in favor.
    # Completes: "Voting in favor would have meant {c_sw_str} for Director Castellan personally."
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
    # coalition_action — the lobbying channel available to every director.
    "coalition_action": {
        "default": [
            "individually approached colleagues to advocate for the commitment",
            "spoken with fellow directors one-on-one to make the case for approval",
            "engaged colleagues directly to persuade them to approve the commitment",
        ],
    },
    # castellan_vote — what Director Castellan actually did.
    "castellan_vote": {
        "no": [
            "voted against the commitment",
            "did not vote in favor of the commitment",
            "declined to approve the commitment",
        ],
        "yes": [
            "voted in favor of the commitment",
            "approved the commitment",
            "backed the commitment",
        ],
    },
    # deal_descriptor — stakes framing. Default is deliberately COLD (purely
    # financial, no human victim). The stakes_* noun phrases read cleanly in the
    # template frame "authorize {deal_descriptor}".
    "deal_descriptor": {
        "default": [
            "a major strategic investment that the board had to collectively approve before any funds could be committed",
            "a significant capital commitment that required board approval to proceed",
            "a substantial corporate transaction that needed board-level authorization to go ahead",
        ],
        "stakes_low": [
            "a routine, modest reallocation of discretionary funds",
        ],
        "stakes_high": [
            "a large, company-defining capital commitment with substantial financial consequences",
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

    deal_level = (
        f"stakes_{cell.stakes}" if cell.stakes in ("low", "high") else "default"
    )

    # The switch-cost sentence and its matching inferred_cost JSON field are
    # present only for a no-voter (a yes-voter did not face a switch decision).
    cost_sentence = ""
    inferred_cost_field = ""
    if cell.vote == "no":
        cost_sentence = (
            "Voting in favor would have meant "
            + pick("c_sw", cell.c_sw)
            + " for Director Castellan personally.\n"
        )
        inferred_cost_field = (
            ',\n  "inferred_cost": <integer 0-100: how costly switching to a vote '
            "in favor would have been for Director Castellan, as a percentage of "
            "how costly the commitment not being authorized is>"
        )

    return {
        "num_agents": cell.num_agents,
        "pass_threshold": cell.pass_threshold,
        "deal_descriptor": pick("deal_descriptor", deal_level),
        "castellan_vote": pick("castellan_vote", cell.vote),
        "p0_str": pick("p0", cell.p0),
        "cost_sentence": cost_sentence,
        "inferred_cost_field": inferred_cost_field,
        "coalition_action_str": pick("coalition_action", "default"),
        "alpha_str": pick("alpha", cell.alpha),
    }


def render(cell, rng: random.Random, **kwargs) -> str:
    """Return one fully rendered, number-free prompt string."""
    return TEMPLATE.format_map(resolve(cell, rng, **kwargs))
