"""
Orchestrator: the conductor agent from the architecture diagram.

It owns the workflow: route a customer through intake -> screening -> risk ->
decision, accumulating a shared context, then attach the explainability narrative.
Because every agent shares one audit trail and one context contract, the
orchestrator stays thin — which is the point. The intelligence lives in
swappable specialists; the orchestrator just guarantees order and traceability.
"""

from agents.intake_agent import IntakeAgent
from agents.screening_agent import ScreeningAgent
from agents.risk_scoring_agent import RiskScoringAgent
from agents.decision_agent import DecisionAgent
from governance import explainability


class Orchestrator:
    def __init__(self, audit):
        self.audit = audit
        self.intake = IntakeAgent(audit)
        self.screening = ScreeningAgent(audit)
        self.risk = RiskScoringAgent(audit)
        self.decision = DecisionAgent(audit)

    def process(self, customer: dict) -> dict:
        context = {"customer": customer}
        context["intake"] = self.intake.run(context)
        context["screening"] = self.screening.run(context)
        context["risk"] = self.risk.run(context)
        context["decision"] = self.decision.run(context)

        narrative = explainability.render(
            customer, context["screening"], context["risk"], context["decision"])

        # Aggregate the FEAT principles touched across this customer's audit events
        principles = sorted({p for e in self.audit.for_customer(customer["customer_id"])
                             for p in e["feat_tags"]["principles"]})

        return {
            "customer_id": customer["customer_id"],
            "name": customer["full_name"],
            "outcome": context["decision"]["outcome"],
            "risk_band": context["risk"]["band"],
            "risk_score": context["risk"]["score"],
            "factors": context["risk"]["factors"],
            "confidence": context["decision"]["confidence"],
            "human_review_required": context["decision"]["human_review_required"],
            "explanation": narrative,
            "decision_drivers": context["decision"]["decision_drivers"],
            "feat_principles": principles,
            "audit_entries": [e["entry_hash"][:12]
                              for e in self.audit.for_customer(customer["customer_id"])],
        }
