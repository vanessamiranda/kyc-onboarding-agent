"""
KYC Agentic MVP — demo runner.

Run:  python run_demo.py

Produces a console dashboard plus two artifacts in outputs/:
  - decisions.json   (per-customer outcomes + explanations)
  - audit_trail.json (tamper-evident, hash-chained event log)
"""

import json
from pathlib import Path
from collections import Counter

from governance.audit_trail import AuditTrail
from agents.orchestrator import Orchestrator

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
SHOWCASE_IDS = {"CUST-00001", "CUST-00002", "CUST-00003",
                "CUST-00004", "CUST-00005", "CUST-00006"}


def bar(label, n, total, width=30):
    fill = int(width * n / total) if total else 0
    return f"  {label:16s} {'█'*fill}{'·'*(width-fill)} {n:3d} ({n/total*100:4.1f}%)"


def main():
    customers = json.loads((DATA / "customers.json").read_text())
    audit = AuditTrail()
    orch = Orchestrator(audit)

    results = [orch.process(c) for c in customers]
    total = len(results)

    print("\n" + "=" * 64)
    print("  KYC ONBOARDING AGENT — BATCH RESULTS")
    print(f"  {total} synthetic applications processed")
    print("=" * 64)

    outcomes = Counter(r["outcome"] for r in results)
    order = ["APPROVE_STP", "REVIEW", "ESCALATE_EDD", "REJECT_AND_REPORT"]
    print("\n  Disposition breakdown")
    for o in order:
        print(bar(o, outcomes.get(o, 0), total))

    stp = outcomes.get("APPROVE_STP", 0)
    human = sum(1 for r in results if r["human_review_required"])
    print(f"\n  Straight-through processing (STP) rate : {stp/total*100:4.1f}%")
    print(f"  Routed to a human officer              : {human}/{total}")

    bands = Counter(r["risk_band"] for r in results)
    print("\n  Risk band distribution")
    for b in ["Low", "Medium", "High"]:
        print(bar(b, bands.get(b, 0), total))

    # ---- Showcase the planted edge cases ----
    print("\n" + "=" * 64)
    print("  SHOWCASE CASES (the ones to narrate in an interview)")
    print("=" * 64)
    for r in results:
        if r["customer_id"] in SHOWCASE_IDS:
            print(f"\n  [{r['customer_id']}] {r['name']}  ->  {r['outcome']}  "
                  f"(risk {r['risk_band']} {r['risk_score']}/100, "
                  f"conf {r['confidence']})")
            print(f"      {r['explanation']}")

    # ---- Governance: prove the audit trail is intact, then prove it detects tampering ----
    print("\n" + "=" * 64)
    print("  GOVERNANCE — AUDIT TRAIL INTEGRITY")
    print("=" * 64)
    print(f"  Total audit events logged : {len(audit.export()['entries'])}")
    print(f"  Hash chain verified       : {audit.verify_integrity()}")

    # Tamper demonstration: secretly flip a decision in the log
    if audit._entries:
        victim = next((e for e in audit._entries
                       if e["action"] == "decision"), audit._entries[0])
        original = json.dumps(victim["output"])
        victim["output"] = {"outcome": "APPROVE_STP", "tampered": True}
        print(f"  [Simulating tampering: forcibly altering one decision entry...]")
        print(f"  Hash chain verified after tamper : {audit.verify_integrity()}  "
              f"<-- breach detected")
        victim["output"] = json.loads(original)  # restore for clean export

    # ---- Export artifacts ----
    OUT.mkdir(exist_ok=True)
    (OUT / "decisions.json").write_text(json.dumps(results, indent=2))
    (OUT / "audit_trail.json").write_text(json.dumps(audit.export(), indent=2))
    print(f"\n  Artifacts written to: {OUT}/")
    print("    - decisions.json   (outcomes + plain-English explanations)")
    print("    - audit_trail.json (tamper-evident event log)\n")


if __name__ == "__main__":
    main()
