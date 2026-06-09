"""
Explainability: the "regulatory explainer" from the architecture diagram.

Every decision must be defensible to (a) the customer, (b) a compliance officer,
and (c) a regulator on inspection. This module renders the structured decision
into a plain-English narrative WITHOUT inventing anything — it only restates the
factors the rules already used. That distinction (narrate, never fabricate) is
the heart of trustworthy AI in a regulated setting.
"""


def render(customer, screening, risk, decision):
    name = customer["full_name"]
    lines = [f"Decision for {name} ({customer['customer_id']}): "
             f"{decision['outcome']}."]

    # Screening narrative
    if screening["sanctions"]["hit"]:
        m = screening["sanctions"]["match"]
        lines.append(
            f"Sanctions: confirmed match to '{m['name']}' on "
            f"{m['list']} (DOB corroborated), program: {m['program']}.")
    elif screening["sanctions"]["near_miss"]:
        lines.append(
            "Sanctions: a name-only near match was found but the date of birth "
            "did not corroborate, so it is treated as a false positive.")
    else:
        lines.append("Sanctions: no match against screened lists.")

    if screening["pep"]["hit"]:
        p = screening["pep"]["match"]
        lines.append(f"PEP: identified as a Politically Exposed Person "
                     f"({p['position']}, {p['country']}) — enhanced due "
                     f"diligence is mandatory.")

    if screening["adverse_media"]["hit"]:
        a = screening["adverse_media"]["match"]
        lines.append(f"Adverse media: {a['severity']} severity item found "
                     f"('{a['headline']}') — flagged for analyst review.")

    # Risk narrative
    lines.append(
        f"Risk rating: {risk['band']} ({risk['score']}/100). "
        f"Main drivers: {', '.join(risk['top_factors'])}.")

    # Decision narrative
    lines.append(f"Required action: {decision['required_action']}.")
    if decision["human_review_required"]:
        lines.append("Routed to a human officer because: "
                     + "; ".join(decision["human_review_reasons"]) + ".")

    return " ".join(lines)
