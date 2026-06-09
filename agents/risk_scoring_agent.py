"""
Risk scoring agent: a transparent, weighted risk model.

DESIGN CHOICE: this is deliberately a rule-based weighted score, not an opaque
ML model. For a regulated KYC decision, explainability and reproducibility beat
marginal accuracy gains. Each point of risk is attributable to a named factor,
and we explicitly EXCLUDE protected attributes (race, religion, gender) — country
risk reflects FATF lists, not ethnicity. That is a defensible fairness posture.
"""

from agents.base import BaseAgent
from governance import feat_mapper

HIGH_RISK_COUNTRIES = {"IR", "KP", "MM", "SY", "AF"}
MEDIUM_RISK_COUNTRIES = {"KH", "PK", "NG", "VE"}
HIGH_RISK_INDUSTRIES = {"Precious Metals & Stones", "Gaming",
                        "Money Services Business", "Art & Antiquities",
                        "Virtual Assets"}


class RiskScoringAgent(BaseAgent):
    name = "RiskScoringAgent"
    action = "risk_scoring"

    def run(self, context):
        customer = context["customer"]
        screening = context["screening"]
        factors = {}

        # Geography
        country = customer["residence_country"]
        if country in HIGH_RISK_COUNTRIES:
            factors["High-risk jurisdiction"] = 35
        elif country in MEDIUM_RISK_COUNTRIES:
            factors["Medium-risk jurisdiction"] = 15

        # Industry / occupation
        if customer["industry"] in HIGH_RISK_INDUSTRIES:
            factors["High-risk industry"] = 25

        # Wealth vs declared income (simple plausibility check)
        if customer["source_of_wealth"] in ("Inheritance", "Sale of property"):
            factors["Lump-sum source of wealth"] = 8
        if customer["annual_income_sgd"] >= 500_000:
            factors["High net worth (EDD trigger)"] = 10

        # Screening outcomes feed the score
        if screening["pep"]["hit"]:
            factors["Politically exposed person"] = 30
        if screening["adverse_media"]["hit"]:
            factors["Adverse media"] = 20
        if screening["sanctions"]["near_miss"]:
            factors["Unresolved name match"] = 12

        score = min(sum(factors.values()), 100)
        band = "High" if score >= 50 else "Medium" if score >= 25 else "Low"
        top = sorted(factors, key=factors.get, reverse=True)[:3] or ["No elevated factors"]

        output = {
            "score": score,
            "band": band,
            "factors": factors,
            "top_factors": top,
            "fairness_note": feat_mapper.fairness_note(),
        }
        self.audit.log(
            customer_id=customer["customer_id"],
            agent=self.name,
            action=self.action,
            inputs={"country": country, "industry": customer["industry"]},
            output={"score": score, "band": band, "factors": factors},
            feat_tags=feat_mapper.tag(self.action),
        )
        return output
