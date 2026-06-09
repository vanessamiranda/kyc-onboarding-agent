# KYC Onboarding Agent — a governance-first agentic MVP

A working, multi-agent KYC (Know Your Customer) onboarding system you can run in
one command, demo in a browser, and defend in an interview. It processes synthetic
customer applications through specialist agents — intake, screening, risk scoring,
decision — and wraps every step in a governance layer mapped to **MAS FEAT** and
the **NIST AI RMF**, with a **tamper-evident audit trail**.

It is built to answer the question a banking hiring manager actually cares about:
*not "is your AI clever?" but "can you prove what it did, and what happens when it
is unsure?"*

---

## Run it in 60 seconds

```bash
cd kyc-agentic-mvp
python3 data/generate_synthetic_data.py   # 1. create synthetic dataset (zero PII)
python3 run_demo.py                        # 2. process the batch + see the dashboard
python3 build_dashboard.py                 # 3. build the interactive browser demo
```

Then open `outputs/kyc_dashboard.html` in any browser — no server, no internet.
Click a case, read the decision and its plain-English rationale, then hit
**Simulate tampering** on the audit ledger and watch the integrity badge break.

No `pip install` needed: the engine is pure standard library on purpose, so it
runs anywhere, offline. (See `requirements.txt` for the optional production path.)

---

## Why this wows (and why it is honest)

Most "AI agent" demos are a single LLM call dressed up. In regulated banking that
is a liability, not an asset. This MVP makes three senior-level moves instead:

1. **The regulated decision is deterministic and reproducible.** Screening and
   risk scoring use transparent rules, so every outcome is attributable to a named
   factor. An LLM is positioned only as an *optional* narrative/triage layer, never
   as the thing that silently approves or declines a customer. Knowing *where not
   to put the model* is the senior signal.
2. **Uncertainty is a routable outcome, not a silent failure.** Incomplete data,
   ambiguous name matches, sanctions/PEP hits — all force human-in-the-loop. The
   system is allowed to say "I'm not sure, a person decides this one."
3. **Everything is provable after the fact.** The hash-chained audit trail means
   the log cannot be edited without detection. That single property is what turns
   a demo into something a bank's compliance function will respect.

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
| Orchestrator | `agents/orchestrator.py` | The conductor: routes a customer through every agent, accumulates a shared context, attaches the narrative. |
| Intake agent | `agents/intake_agent.py` | Validates the application; gates on data completeness. |
| Screening agent | `agents/screening_agent.py` | Sanctions, PEP and adverse-media checks with **false-positive suppression** via DOB corroboration. |
| Risk scoring agent | `agents/risk_scoring_agent.py` | Transparent weighted score; protected attributes explicitly excluded. |
| Decision agent | `agents/decision_agent.py` | Severity-first, reproducible disposition with mandatory human gates. |
| Audit trail | `governance/audit_trail.py` | Append-only, hash-chained, tamper-evident event log. |
| FEAT mapper | `governance/feat_mapper.py` | Tags each action to MAS FEAT + NIST AI RMF principles. |
| Guardrails | `governance/guardrails.py` | Completeness gate, confidence floor, mandatory-escalation triggers. |
| Explainability | `governance/explainability.py` | Plain-English rationale a human officer can sign. |

---

## How it was built, step by step

This is the order to build it in yourself — each step is independently runnable,
which is how you keep an MVP honest.

**Step 1 — Synthetic data as a governance feature.** Real customer data in a demo
is a PDPA/GDPR breach waiting to happen. `data/generate_synthetic_data.py` creates
a reproducible (seeded) dataset where every record is flagged `synthetic: True`.
Critically, it *plants edge cases* — a confirmed sanctions match, a near-miss, a
PEP, a high-risk-jurisdiction customer, an adverse-media hit, and an incomplete
application — so the agent has a real story to tell, plus a population of ordinary
low-risk customers so you can measure a believable straight-through-processing rate.

**Step 2 — The governance layer first, not last.** Build the audit trail, FEAT
mapper, guardrails and explainability *before* the agents, then make every agent
write through them. Governance bolted on at the end is theatre; governance the
agents are forced to use is real. The audit trail chains each event's SHA-256 hash
into the next, so altering any historical entry breaks every downstream link.

**Step 3 — Specialist agents behind one contract.** Each agent takes a shared
`context` dict, does one job, logs to the audit trail, and returns its findings.
A uniform contract is what lets the orchestrator treat agents as interchangeable
parts — you can swap the rule-based risk model for an ML one without touching
anything else.

**Step 4 — The screening that separates juniors from seniors.** Anyone can match
names. The hard part is *not* drowning compliance in false positives. The screening
agent treats a strong name match with a mismatched date of birth as a *near miss*,
not a hit — and records that it considered and dismissed it. Watch `CUST-00002`
(Viktor Petroff) get correctly cleared while `CUST-00001` (Viktor Petrov) is blocked.

**Step 5 — Decisions that never silently auto-decline.** The decision agent is
ordered by severity and fully reproducible. A confidence proxy (built from
inspectable signals, not an opaque model score) plus mandatory triggers decide
whether a human must sign off. Sanctions, PEP and high-severity adverse media
*always* see a person.

**Step 6 — Make it visible.** `build_dashboard.py` runs the pipeline and injects
the real results into a single self-contained HTML file — the demo you actually
open in front of people.

---

## The showcase cases (what to narrate)

| Case | Profile | Outcome | The point |
|---|---|---|---|
| `CUST-00001` Viktor Petrov | Exact sanctions match, DOB corroborated | **REJECT + REPORT** | Confirmed hits are blocked and escalated to the MLRO. |
| `CUST-00002` Viktor Petroff | Same name, different DOB | **APPROVE (STP)** | False-positive suppression — the system doesn't escalate noise. |
| `CUST-00003` Daniel Reyes | Politically Exposed Person | **ESCALATE (EDD)** | PEP status forces enhanced due diligence, never a silent decline. |
| `CUST-00004` | High-risk country + industry | **ESCALATE (EDD)** | Risk score crosses the High band on transparent factors. |
| `CUST-00005` Marcus Goh | High-severity adverse media | **ESCALATE (EDD)** | Negative news triaged with source + severity retained for review. |
| `CUST-00006` | Unverified ID document | **REVIEW** | Incomplete data drops below the confidence floor → human decides. |

---

## Governance, in regulator language

- **Fairness (F)** — risk scoring excludes race, religion, gender and nationality
  as standalone drivers. Country risk reflects FATF jurisdiction lists, not ethnicity.
- **Ethics (E)** — screening evidences matches rather than asserting them; PEPs get
  due diligence, not exclusion.
- **Accountability (A)** — every action is logged with who/what produced it and
  whether a human was required. The hash chain proves the log is intact.
- **Transparency (T)** — every decision ships with a plain-English rationale and
  the exact factors that drove it.
- **NIST AI RMF** — each action also maps to MAP / MEASURE / MANAGE / GOVERN for an
  international audience.

---

## Interview talking points (the hard questions, answered)

**"Why rules instead of an LLM for the decision?"**
Because a KYC disposition has to be reproducible and explainable to a regulator. I
use deterministic rules for the regulated call and reserve the LLM for unstructured
triage and narration, where a wrong answer is reviewable rather than binding. That
boundary is a design decision, not a limitation.

**"How do you prevent the audit log being doctored?"**
Hash chaining. Each entry includes the previous entry's hash, so editing any past
record changes its hash and breaks every link after it. The dashboard's "Simulate
tampering" button demonstrates the detection live.

**"How do you handle false positives in screening?"**
Date-of-birth corroboration before confirming a match, with name-only near misses
surfaced separately so an analyst can see what was considered and dismissed. The
match threshold is a single tunable parameter for the precision/recall tradeoff.

**"What happens when the model is unsure?"**
Uncertainty is an outcome. A completeness gate blocks decisions on missing data, a
confidence floor routes low-confidence cases to a human, and sanctions/PEP/adverse
media always escalate regardless of confidence.

**"How would this scale to production?"**
Swap `difflib` for a vendor screening engine or `rapidfuzz`; connect real OFAC/UN/EU
and PEP feeds; persist the audit chain to a write-once store; wrap the orchestrator
in FastAPI; add the LLM adverse-media summariser behind the existing interface. The
contracts don't change — that's the payoff of the agent/governance separation.

---

## Honest limitations (say these before you're asked)

- The lists, customers and adverse media are **synthetic** — the matching logic is
  real, the data is not.
- The confidence score is a transparent proxy, not a calibrated model probability.
- The hash chain is tamper-*evident*, not tamper-*proof*; production needs a
  write-once or externally-witnessed store.
- This is an MVP to demonstrate architecture and governance thinking, not a
  production AML system.

---

*Built as a portfolio demonstrator. All data is synthetic; no real persons are
represented.*
