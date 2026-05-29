"""Scenario s02 — placeholder (to be designed later).

Implement the same interface as prompts/s01_health/scenario.py:
    TEMPLATE, PHRASINGS, render(cell, rng, **kwargs)
Keep it structurally isomorphic to the committee example but in a different
surface domain (e.g. a funding/grant committee), so findings can be checked for
generalization across narratives.
"""

from __future__ import annotations

TEMPLATE = ""
PHRASINGS: dict[str, dict] = {}


def render(cell, rng, **kwargs) -> str:  # noqa: D401, ARG001
    raise NotImplementedError("Scenario s02 is not implemented yet.")
