"""
Guardrails: the "AI output monitor" from the architecture diagram.

In a regulated context the question is never "is the model smart?" but "what
happens when it is unsure or wrong?" These guardrails make uncertainty a
first-class, routable outcome rather than a silent failure:

  - data completeness gate (you cannot decide on missing facts)
  - confidence floor (below it, a human decides)
  - mandatory-escalation triggers (sanctions / PEP always see a human)

This is the part that separates a compliance-grade system from a chatbot.
"""

CONFIDENCE_FLOOR = 0.70          # below this, route to a human
MANDATORY_HUMAN_TRIGGERS = {"SANCTIONS_HIT", "PEP", "ADVERSE_MEDIA_HIGH"}


def completeness_gate(customer: dict):
    """Return (ok, missing_fields). Missing data must never be auto-decided."""
    required = ["full_name", "date_of_birth", "residence_country",
                "occupation", "source_of_wealth"]
    missing = [f for f in required if not customer.get(f)]
    if not customer.get("id_document", {}).get("verified", False):
        missing.append("verified_id_document")
    return (len(missing) == 0, missing)


def confidence_for(signals: dict) -> float:
    """
    A transparent confidence proxy. We are deliberately NOT using an opaque
    model probability here — confidence falls when data is incomplete or when
    screening produced ambiguous (fuzzy) matches that need a human eye.
    """
    conf = 1.0
    if not signals.get("data_complete", True):
        conf -= 0.4
    if signals.get("fuzzy_match_ambiguous", False):
        conf -= 0.25
    if signals.get("adverse_media_unverified", False):
        conf -= 0.15
    return round(max(conf, 0.0), 2)


def requires_human(decision_drivers: set, confidence: float):
    """Returns (human_required, reasons)."""
    reasons = []
    triggered = decision_drivers & MANDATORY_HUMAN_TRIGGERS
    if triggered:
        reasons.append(f"Mandatory review trigger(s): {', '.join(sorted(triggered))}")
    if confidence < CONFIDENCE_FLOOR:
        reasons.append(f"Confidence {confidence} below floor {CONFIDENCE_FLOOR}")
    return (len(reasons) > 0, reasons)
