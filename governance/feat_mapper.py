"""
MAS FEAT principle mapper.

The Monetary Authority of Singapore's FEAT principles (Fairness, Ethics,
Accountability, Transparency) are THE governance vocabulary for AI in Singapore
financial services. NIST AI RMF (GOVERN/MAP/MEASURE/MANAGE) is the global
equivalent. Mapping each agent action to both is what lets a candidate say in an
interview: "every automated step is traceable to a named regulatory principle,"
which is exactly the language a Head of Compliance wants to hear.

This module is intentionally simple — a lookup, not magic. Governance maturity
shows up in DISCIPLINE (every action tagged), not cleverness.
"""

FEAT = {
    "F": "Fairness",
    "E": "Ethics",
    "A": "Accountability",
    "T": "Transparency",
}

# Map each agent action to the FEAT principles it primarily serves,
# plus the corresponding NIST AI RMF function for an international audience.
ACTION_MAP = {
    "intake_validation": {
        "feat": ["A", "T"],
        "nist": "MAP",
        "note": "Inputs validated and recorded before any decision is made.",
    },
    "sanctions_screening": {
        "feat": ["E", "A"],
        "nist": "MEASURE",
        "note": "Screening against authoritative lists; matches evidenced, not asserted.",
    },
    "pep_screening": {
        "feat": ["E", "A"],
        "nist": "MEASURE",
        "note": "PEP status drives mandatory enhanced due diligence, never silent decline.",
    },
    "adverse_media_screening": {
        "feat": ["E", "T"],
        "nist": "MEASURE",
        "note": "Negative news triaged with source and severity retained for review.",
    },
    "risk_scoring": {
        "feat": ["F", "T"],
        "nist": "MEASURE",
        "note": "Score built from declared, inspectable factors; no protected attributes used.",
    },
    "decision": {
        "feat": ["A", "T"],
        "nist": "MANAGE",
        "note": "Decision is rule-based and reproducible; rationale attached.",
    },
    "human_escalation": {
        "feat": ["A"],
        "nist": "MANAGE",
        "note": "Low-confidence or high-impact cases routed to a human officer.",
    },
}


def tag(action: str):
    """Return the FEAT/NIST tags for a given agent action."""
    entry = ACTION_MAP.get(action, {"feat": ["A"], "nist": "GOVERN",
                                     "note": "Action logged for accountability."})
    return {
        "principles": [FEAT[p] for p in entry["feat"]],
        "nist_function": entry["nist"],
        "rationale": entry["note"],
    }


def fairness_note():
    """Explicit statement of what the model does NOT use — bias-by-omission guard."""
    return ("Risk scoring excludes race, religion, gender and nationality as "
            "standalone risk drivers. Country risk reflects FATF jurisdiction "
            "lists, not the customer's ethnicity.")
