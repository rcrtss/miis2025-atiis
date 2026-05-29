"""Ground-truth Shapley blame for the focal agent, from the formal framework.

This is the ONLY place in the experiment where ordinal ids become numbers.

    The reference tables below are a MODELLING ASSUMPTION used to compute the
    formal oracle. They are NOT a claim that the phrasing "low" equals p0 = 0.10.
    Whether the model reads a phrasing as the intended level is exactly what the
    experiment tests (see `inferred_probability`). Accordingly:

      - oracle_blame(cell)                     uses the reference value (our nominal mapping)
      - oracle_blame(cell, p0_value=x)         uses an externally supplied probability,
                                               e.g. the model's OWN inferred_probability/100,
                                               which makes no assumption at all.

Wraps `framework/committee.py` (the BlameCalculator + EpistemicState from
Friedenberg & Halpern 2019), which natively supports a variable threshold.
"""

from __future__ import annotations

import sys
from pathlib import Path

# committee.py lives in the sibling `framework/` directory of the repo root.
_FRAMEWORK = Path(__file__).resolve().parents[2] / "framework"
if str(_FRAMEWORK) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK))

from committee import BlameCalculator, EpistemicState  # noqa: E402

from engine.params import Cell  # noqa: E402

# ── Reference values (oracle-only; NOT semantic claims) ───────────────────────
P0_REFERENCE: dict[str, float] = {
    "very_low":      0.10,
    "low":           0.20,
    "somewhat_low":  0.35,
    "even":          0.50,
    "somewhat_high": 0.60,
    "high":          0.80,
    "very_high":     0.90,
}

CSW_REFERENCE: dict[str, int] = {
    "trivial":     200,
    "minor":       500,
    "significant": 2000,
    "severe":      3000,
}

ALPHA_REFERENCE: dict[str, float] = {
    "negligible": 0.01,
    "slim":       0.03,
    "modest":     0.05,
    "strong":     0.10,
}

# Framework constants held fixed across the current sweeps.
N_BALANCE = 5000   # balance parameter N (must exceed the largest cost)
C_PRESSURE = 100   # per-agent cost of applying social pressure


def oracle_blame(cell: Cell, p0_value: float | None = None) -> float:
    """Individual Shapley blame for the focal agent (ag1) under `cell`.

    `p0_value` overrides the reference probability for the focal agent's belief
    about the *other* agents. Pass the model's inferred_probability/100 to get
    an assumption-free oracle comparison.
    """
    agents = [f"ag{i}" for i in range(1, cell.num_agents + 1)]
    focal = agents[0]

    p0 = P0_REFERENCE[cell.p0] if p0_value is None else p0_value

    calc = BlameCalculator(
        agents,
        balance_parameter_N=N_BALANCE,
        pressure_effect=ALPHA_REFERENCE[cell.alpha],
        pressure_cost=C_PRESSURE,
        switch_cost=CSW_REFERENCE[cell.c_sw],
    )

    probs = {ag: p0 for ag in agents}
    probs[focal] = 1.0 if cell.vote == "yes" else 0.0   # focal knows own vote
    e1 = EpistemicState(probs, threshold=cell.pass_threshold)

    return calc.apportion_blame_shapley(focal, e1)
