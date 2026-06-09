"""
Decision agent: the regulated call.

Outcomes map to real KYC dispositions:
  - REJECT_AND_REPORT : confirmed sanctions match (block + file SAR-style report)
  - ESCALATE_EDD      : PEP / high risk / adverse media -> enhanced due diligence
  - REVIEW            : low confidence or incomplete -> human officer decides
  - APPROVE_STP       : clean, low-risk -> straight-through processing

The decision itself is deterministic and ordered by severity, so it is fully
reproducible and explainable. The confidence proxy and mandatory triggers decide
whether a human must sign off — the model never silently auto-declines anyone.
"""

from agents.base import BaseAgent
from governance import feat_mapper, guardrails


class DecisionAgent(BaseAgent):
    name = "DecisionAgent"
    action = "decision"

    def run(self, context):
        customer = context["customer"]
        intake = context["intake"]
        screening = context["screening"]
        risk = context["risk"]

        drivers = set()
        if screening["sanctions"]["hit"]:
            drivers.add("SANCTIONS_HIT")
        if screening["pep"]["hit"]:
            drivers.add("PEP")
        if screening["adverse_media"]["hit"] and \
                screening["adverse_media"]["match"]["severity"] == "High":
            drivers.add("ADVERSE_MEDIA_HIGH")

        # Confidence proxy from inspectable signals
        confidence = guardrails.confidence_for({
            "data_complete": intake["data_complete"],
            "fuzzy_match_ambiguous": screening["sanctions"]["near_miss"],
            "adverse_media_unverified": screening["adverse_media"]["hit"],
        })
        human_required, human_reasons = guardrails.requires_human(drivers, confidence)

        # Ordered, severity-first decision logic
        if "SANCTIONS_HIT" in drivers:
            outcome = "REJECT_AND_REPORT"
            action_text = ("Block onboarding, freeze any pending activity, and "
                           "escalate to the MLRO for regulatory reporting.")
        elif not intake["data_complete"]:
            outcome = "REVIEW"
            action_text = (f"Request missing items: "
                           f"{', '.join(intake['missing_fields'])}.")
        elif "PEP" in drivers or risk["band"] == "High" or "ADVERSE_MEDIA_HIGH" in drivers:
            outcome = "ESCALATE_EDD"
            action_text = ("Apply enhanced due diligence: senior management "
                           "sign-off, source-of-wealth corroboration, ongoing "
                           "monitoring at elevated frequency.")
        elif risk["band"] == "Medium" or confidence < guardrails.CONFIDENCE_FLOOR:
            outcome = "REVIEW"
            action_text = "Standard due diligence with analyst confirmation."
        else:
            outcome = "APPROVE_STP"
            action_text = ("Approve via straight-through processing; standard "
                           "periodic review cycle.")

        # A REVIEW/ESCALATE outcome always means a human is in the loop
        if outcome in ("REVIEW", "ESCALATE_EDD", "REJECT_AND_REPORT"):
            human_required = True
            if not human_reasons:
                human_reasons = [f"Outcome '{outcome}' requires officer sign-off"]

        output = {
            "outcome": outcome,
            "required_action": action_text,
            "decision_drivers": sorted(drivers),
            "confidence": confidence,
            "human_review_required": human_required,
            "human_review_reasons": human_reasons,
        }
        self.audit.log(
            customer_id=customer["customer_id"],
            agent=self.name,
            action=self.action,
            inputs={"risk_band": risk["band"], "drivers": sorted(drivers)},
            output=output,
            feat_tags=feat_mapper.tag(self.action),
            confidence=confidence,
            human_review=human_required,
        )
        if human_required:
            self.audit.log(
                customer_id=customer["customer_id"],
                agent=self.name,
                action="human_escalation",
                inputs={"outcome": outcome},
                output={"reasons": human_reasons},
                feat_tags=feat_mapper.tag("human_escalation"),
                human_review=True,
            )
        return output
