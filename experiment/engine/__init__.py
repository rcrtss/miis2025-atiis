"""Scenario-agnostic machinery for the blameworthiness sweeps.

Nothing in this package knows about any specific vignette. Scenarios live under
`prompts/<scenario>/scenario.py` and expose a common interface (TEMPLATE,
PHRASINGS, render). Run knobs live in `sweeps/<sweep>.py`.
"""
