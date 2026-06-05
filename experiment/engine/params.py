"""The unit of an experiment: one `Cell`.

A Cell is described entirely in *prompt-safe* terms:

  - Subjective/belief parameters (p0, c_sw, alpha) are ORDINAL IDS, e.g. "low",
    "significant", "modest". They map to natural-language wordings in the
    scenario's PHRASINGS table. No number is attached here, on purpose: claiming
    `low == 0.10` is the hypothesis under test, not a fact we encode.
  - Objective scenario facts (num_agents, pass_threshold) are genuine integers,
    because "at least 4 of 7 physicians" is a fact of the world, not a
    belief-to-vibe mapping. These may legitimately appear in the prompt.

The numeric values needed to compute the formal oracle live ONLY in
`engine/oracle.py`, clearly flagged as a modelling reference, never here and
never in a rendered prompt.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Cell:
    """One experimental condition, in prompt-safe (number-free) terms.

    Defaults reproduce the paper's baseline focal agent (ag1: voted no,
    moderately optimistic). The runner overrides whatever the sweep varies.
    """

    p0: str = "somewhat_high"   # ordinal id  -> PHRASINGS["p0"][p0]
    c_sw: str = "significant"   # ordinal id  -> PHRASINGS["c_sw"][c_sw]
    alpha: str = "modest"       # ordinal id  -> PHRASINGS["alpha"][alpha]
    vote: str = "no"            # "no" | "yes"
    stakes: str = "default"     # "default" | "low" | "high"
    num_agents: int = 7         # objective fact (may appear in prompt)
    pass_threshold: int = 4     # objective fact (may appear in prompt)


@dataclass(frozen=True)
class Arm:
    """One OFAT validation arm: the whole sweep re-run with `overrides` applied.

    `name` identifies the arm in the file tree and manifest; `overrides` is a
    dict of Cell fields to change relative to the sweep's HELD baseline (empty
    for the baseline arm). Exactly one field changes per arm, by convention, so
    any shift in the LLM's blame curve is attributable to that single variable.
    """

    name: str
    overrides: dict = field(default_factory=dict)
