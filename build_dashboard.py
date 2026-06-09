"""
Builds the standalone interactive dashboard (single self-contained .html file).

Run:  python build_dashboard.py
Output: outputs/kyc_dashboard.html  — open it in any browser, no server needed.
"""

import json
from pathlib import Path

from governance.audit_trail import AuditTrail
from agents.orchestrator import Orchestrator

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
SHOWCASE = {"CUST-00001", "CUST-00002", "CUST-00003",
            "CUST-00004", "CUST-00005", "CUST-00006"}


def main():
    customers = json.loads((DATA / "customers.json").read_text())
    audit = AuditTrail()
    orch = Orchestrator(audit)
    decisions = []
    for c in customers:
        r = orch.process(c)
        r["showcase"] = r["customer_id"] in SHOWCASE
        decisions.append(r)

    payload = {"decisions": decisions, "audit": audit.export()}
    template = (ROOT / "dashboard_template.html").read_text()
    html = template.replace("__DATA__", json.dumps(payload))

    OUT.mkdir(exist_ok=True)
    target = OUT / "kyc_dashboard.html"
    target.write_text(html)
    print(f"Dashboard built: {target}")
    print(f"  {len(decisions)} cases, {audit.export()['entry_count']} audit events embedded")
    print(f"  Chain integrity: {audit.verify_integrity()}")


if __name__ == "__main__":
    main()
