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

# Stakes -> balance parameter N. In the framework N controls how much switching
# cost matters relative to the outcome: high N means costs are negligible next
# to what is at stake, low N means they weigh heavily. Stakes is the
# natural-language proxy for N, so the reference oracle maps stakes onto N here.
# Each value must exceed the largest switch cost (CSW_REFERENCE max = 3000).
STAKES_N_REFERENCE: dict[str, int] = {
    "low":      2500,
    "default":  5000,
    "high":    12000,
}

# Per-agent cost of applying social pressure (held fixed across current sweeps).
C_PRESSURE = 100

# Nominal balance parameter (the "default" stakes value); retained as a name for
# external callers and for mapping an inferred cost ratio onto a switch cost.
N_BALANCE = STAKES_N_REFERENCE["default"]


def oracle_blame(
    cell: Cell,
    *,
    p0_value: float | None = None,
    alpha_value: float | None = None,
    csw_over_N: float | None = None,
) -> float:
    """Individual Shapley blame for the focal agent (ag1) under `cell`.

    Each keyword overrides one reference value with an externally supplied one,
    e.g. the model's OWN inferred reading, to get an assumption-free comparison:

      - p0_value     focal agent's belief about the others   (inferred_probability/100)
      - alpha_value  pressure effectiveness alpha             (inferred_alpha/100;
                     the framework natively clamps n*alpha at committee.py)
      - csw_over_N   switch cost as a fraction of N           (inferred_cost/100);
                     mapped to an absolute switch cost as csw_over_N * N.

    With no keywords, every value comes from the reference tables (the nominal
    mapping). N follows the cell's stakes via STAKES_N_REFERENCE.
    """
    agents = [f"ag{i}" for i in range(1, cell.num_agents + 1)]
    focal = agents[0]

    p0 = P0_REFERENCE[cell.p0] if p0_value is None else p0_value
    alpha = ALPHA_REFERENCE[cell.alpha] if alpha_value is None else alpha_value
    n_balance = STAKES_N_REFERENCE[cell.stakes]
    switch_cost = (
        CSW_REFERENCE[cell.c_sw] if csw_over_N is None else csw_over_N * n_balance
    )

    calc = BlameCalculator(
        agents,
        balance_parameter_N=n_balance,
        pressure_effect=alpha,
        pressure_cost=C_PRESSURE,
        switch_cost=switch_cost,
    )

    probs = {ag: p0 for ag in agents}
    probs[focal] = 1.0 if cell.vote == "yes" else 0.0   # focal knows own vote
    e1 = EpistemicState(probs, threshold=cell.pass_threshold)

    return calc.apportion_blame_shapley(focal, e1)
