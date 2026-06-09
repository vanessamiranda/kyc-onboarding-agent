# KYC Onboarding Agent — a governance-first agentic system

A working, multi-agent KYC (Know Your Customer) onboarding system that runs in
one command and ships with an interactive browser demo. It processes synthetic
customer applications through specialist agents — intake, screening, risk
scoring, decision and wraps every step in a governance layer mapped to **MAS
FEAT** and the **NIST AI RMF**, with a **tamper-evident audit trail**.

The design question it answers: in a regulated setting it is not enough for an
AI system to be capable — you have to be able to prove what it did, and define
what happens when it is uncertain.

---

## Run it in 60 seconds

```bash
cd kyc-agentic-mvp
python3 data/generate_synthetic_data.py   # 1. create synthetic dataset (zero PII)
python3 run_demo.py                        # 2. process the batch
python3 build_dashboard.py                 # 3. build the interactive browser demo
```

Then open `outputs/kyc_dashboard.html` in any browser — no server, no internet.
Click a case to read the decision and its plain-English rationale, then use
**Simulate tampering** on the audit ledger to watch the integrity check break.

No `pip install` needed: the engine uses only the Python standard library, so it
runs anywhere, offline. See `requirements.txt` for the optional production path.

---

## Design principles

1. **The regulated decision is deterministic and reproducible.** Screening and
   risk scoring use transparent rules, so every outcome is attributable to a
   named factor. An LLM sits only in an optional narrative/triage layer — never
   in the path that approves or declines a customer.
2. **Uncertainty is a routable outcome.** Incomplete data, ambiguous name
   matches, and sanctions/PEP hits force human review rather than a silent
   decision.
3. **Decisions are provable after the fact.** The hash-chained audit trail means
   a historical entry cannot be altered without detection.

---

## Architecture

```
                         ┌────────────────────────┐
   Application  ───────▶ │      ORCHESTRATOR       │   routes + assembles case file
   (synthetic)           └───────────┬────────────┘
                                     │
         ┌───────────────┬───────────┼───────────────┬──────────────┐
         ▼               ▼           ▼               ▼              ▼
   ┌──────────┐   ┌──────────┐  ┌──────────┐   ┌──────────┐   (explainability
   │  Intake  │   │ Screening│  │   Risk   │   │ Decision │    renders the
   │  agent   │   │  agent   │  │ scoring  │   │  agent   │    rationale)
   └────┬─────┘   └────┬─────┘  └────┬─────┘   └────┬─────┘
        │              │             │              │
        └──────────────┴─────────────┴──────────────┘
                              │  every action writes through
                              ▼
              ╔═══════════════════════════════════════╗
              ║          GOVERNANCE LAYER             ║
              ║  audit trail (hash chain) · FEAT/NIST  ║
              ║  mapper · guardrails · explainability  ║
              ╚═══════════════════════════════════════╝
```

| Component | File | Job |
|---|---|---|
| Orchestrator | `agents/orchestrator.py` | Routes a customer through every agent, accumulates a shared context, attaches the narrative. |
| Intake agent | `agents/intake_agent.py` | Validates the application; gates on data completeness. |
| Screening agent | `agents/screening_agent.py` | Sanctions, PEP and adverse-media checks with false-positive suppression via DOB corroboration. |
| Risk scoring agent | `agents/risk_scoring_agent.py` | Transparent weighted score; protected attributes explicitly excluded. |
| Decision agent | `agents/decision_agent.py` | Severity-first, reproducible disposition with mandatory human gates. |
| Audit trail | `governance/audit_trail.py` | Append-only, hash-chained, tamper-evident event log. |
| FEAT mapper | `governance/feat_mapper.py` | Tags each action to MAS FEAT + NIST AI RMF principles. |
| Guardrails | `governance/guardrails.py` | Completeness gate, confidence floor, mandatory-escalation triggers. |
| Explainability | `governance/explainability.py` | Plain-English rationale a human officer can sign. |

---

## How it works

- **Synthetic data by design.** Real customer data in a demo would be a
  PDPA/GDPR breach. Every record is flagged `synthetic: True`, and the dataset
  deliberately includes edge cases — a confirmed sanctions match, a near-miss, a
  PEP, a high-risk-jurisdiction customer, an adverse-media hit, an incomplete
  application — alongside a population of ordinary low-risk customers so the
  straight-through-processing rate is realistic.
- **Governance is foundational, not bolted on.** Every agent writes through the
  audit trail, FEAT mapper, guardrails and explainability. Each audit event
  chains its SHA-256 hash into the next, so altering any historical entry breaks
  every downstream link.
- **Agents share one contract.** Each takes a shared `context` dict, does one
  job, logs to the audit trail, and returns its findings. That uniform contract
  is what lets the rule-based risk model be swapped for an ML model without
  touching anything else.
- **False-positive suppression in screening.** A strong name match with a
  mismatched date of birth is treated as a *near miss*, not a hit, and recorded
  as considered-and-dismissed — so screening does not drown compliance in noise.
- **No silent auto-decline.** The decision agent is severity-ordered and fully
  reproducible. A confidence proxy (built from inspectable signals, not an opaque
  model score) plus mandatory triggers determine when a human must sign off.

---

## Example cases

| Case | Profile | Outcome | Why |
|---|---|---|---|
| `CUST-00001` Viktor Petrov | Exact sanctions match, DOB corroborated | **REJECT + REPORT** | Confirmed hits are blocked and escalated to the MLRO. |
| `CUST-00002` Viktor Petroff | Same name, different DOB | **APPROVE (STP)** | False-positive suppression — noise is not escalated. |
| `CUST-00003` Daniel Reyes | Politically Exposed Person | **ESCALATE (EDD)** | PEP status forces enhanced due diligence, not a silent decline. |
| `CUST-00004` | High-risk country + industry | **ESCALATE (EDD)** | Risk score crosses the High band on transparent factors. |
| `CUST-00005` Marcus Goh | High-severity adverse media | **ESCALATE (EDD)** | Negative news triaged with source and severity retained. |
| `CUST-00006` | Unverified ID document | **REVIEW** | Incomplete data drops below the confidence floor → human decides. |

---

## Governance (MAS FEAT & NIST AI RMF)

- **Fairness (F)** — risk scoring excludes race, religion, gender and
  nationality as standalone drivers. Country risk reflects FATF jurisdiction
  lists, not ethnicity.
- **Ethics (E)** — screening evidences matches rather than asserting them; PEPs
  receive due diligence, not exclusion.
- **Accountability (A)** — every action is logged with what produced it and
  whether a human was required; the hash chain proves the log is intact.
- **Transparency (T)** — every decision ships with a plain-English rationale and
  the exact factors that drove it.
- **NIST AI RMF** — each action also maps to MAP / MEASURE / MANAGE / GOVERN.

---

## Scope and limitations

- The lists, customers and adverse media are **synthetic** — the matching logic
  is real, the data is not.
- The confidence score is a transparent proxy, not a calibrated model probability.
- The hash chain is tamper-*evident*, not tamper-*proof*; production would need a
  write-once or externally-witnessed store.
- This is a demonstrator of architecture and governance thinking, not a
  production AML system.

## Production path

Swap `difflib` for a vendor screening engine or `rapidfuzz`; connect real
OFAC/UN/EU and PEP feeds; persist the audit chain to a write-once store; wrap the
orchestrator in an API; add an LLM adverse-media summariser behind the existing
interface. The agent and governance contracts do not change.

---

*All data is synthetic; no real persons are represented.*
