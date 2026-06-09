"""Intake agent: validate the application before anything downstream runs."""

from agents.base import BaseAgent
from governance import feat_mapper, guardrails


class IntakeAgent(BaseAgent):
    name = "IntakeAgent"
    action = "intake_validation"

    def run(self, context):
        customer = context["customer"]
        complete, missing = guardrails.completeness_gate(customer)
        output = {
            "data_complete": complete,
            "missing_fields": missing,
        }
        self.audit.log(
            customer_id=customer["customer_id"],
            agent=self.name,
            action=self.action,
            inputs=customer,
            output=output,
            feat_tags=feat_mapper.tag(self.action),
        )
        return output
