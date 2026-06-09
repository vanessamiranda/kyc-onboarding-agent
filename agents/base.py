"""
Base agent and name-matching utilities.

NAME MATCHING WITHOUT A DEPENDENCY
----------------------------------
Real screening engines (e.g. against OFAC) must catch transliteration and
spelling variants — "Viktor Petrov" vs "Victor Petroff". We implement a
transparent similarity score using only the standard library (difflib), with
token sorting so word order doesn't matter. In production you would swap in
rapidfuzz or a vendor engine; the interface stays the same. Keeping it
inspectable is itself a governance choice — no black-box match scores.
"""

from difflib import SequenceMatcher


def normalise(name: str) -> str:
    return " ".join(sorted(name.lower().replace(".", "").replace(",", "").split()))


def name_similarity(a: str, b: str) -> float:
    """0.0–1.0 similarity, order-independent."""
    return round(SequenceMatcher(None, normalise(a), normalise(b)).ratio(), 3)


class BaseAgent:
    """
    Minimal agent contract: a name, and a `run` method that takes a context dict,
    does its job, writes to the shared audit trail, and returns its findings.
    Keeping a uniform contract is what lets the orchestrator treat agents as
    interchangeable, swappable components.
    """
    name = "base"
    action = "base_action"

    def __init__(self, audit):
        self.audit = audit

    def run(self, context: dict) -> dict:  # pragma: no cover - interface
        raise NotImplementedError
