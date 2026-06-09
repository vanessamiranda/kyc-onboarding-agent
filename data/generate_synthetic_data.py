"""
Synthetic data generator for the KYC Agentic MVP.

WHY SYNTHETIC DATA IS A GOVERNANCE FEATURE, NOT A SHORTCUT
----------------------------------------------------------
Building a KYC demo on real customer records would itself be a data-protection
breach (PDPA in Singapore, GDPR in the EU). Generating clearly-labelled fake
data means the system can be demoed, audited and shared with zero PII exposure.
Every record below carries `"synthetic": True` so it can never be mistaken for
production data.

We deliberately PLANT edge cases so the agent has something interesting to do:
  - a confirmed sanctions match
  - a near-miss sanctions match (tests false-positive handling)
  - a Politically Exposed Person (PEP)
  - a high-risk jurisdiction customer
  - an adverse-media hit
  - a low-confidence / incomplete application (tests human-in-the-loop)
The rest are ordinary low-risk customers so we can measure straight-through
processing (STP) rate the way a real bank would.
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)  # reproducibility: same data every run, which auditors love
DATA_DIR = Path(__file__).parent

# --- Name pools (Singapore / SEA banking context + international) -------------
FIRST_NAMES = [
    "Wei", "Mei", "Jun", "Hui", "Siti", "Nurul", "Arjun", "Priya", "Daniel",
    "Sarah", "Marcus", "Aisha", "Ravi", "Lina", "Chen", "Farah", "Kumar",
    "Grace", "Hassan", "Yuki", "Diego", "Olga", "Ahmed", "Chloe", "Ibrahim",
]
LAST_NAMES = [
    "Tan", "Lim", "Lee", "Wong", "Ng", "Rahman", "Sharma", "Abdullah", "Chong",
    "Goh", "Nair", "Hidayat", "Cheng", "Ismail", "Patel", "Koh", "Sinaga",
    "Reyes", "Ivanova", "Al-Farsi", "Nguyen", "Suharto",
]

OCCUPATIONS = [
    ("Software Engineer", "Technology", "low"),
    ("Teacher", "Education", "low"),
    ("Nurse", "Healthcare", "low"),
    ("Marketing Manager", "Retail", "low"),
    ("Accountant", "Professional Services", "low"),
    ("Civil Servant", "Government", "medium"),
    ("Real Estate Agent", "Real Estate", "medium"),
    ("Jewellery Trader", "Precious Metals & Stones", "high"),
    ("Casino Junket Operator", "Gaming", "high"),
    ("Money Services Operator", "Money Services Business", "high"),
    ("Art Dealer", "Art & Antiquities", "high"),
    ("Crypto Fund Manager", "Virtual Assets", "high"),
]

SOURCE_OF_WEALTH = ["Employment", "Business income", "Inheritance",
                    "Investment returns", "Sale of property"]
PRODUCTS = ["Savings Account", "Current Account", "Wealth Management",
            "Credit Card", "Trade Finance Facility"]

# FATF-style higher-risk jurisdiction codes (illustrative, synthetic mapping)
HIGH_RISK_COUNTRIES = ["IR", "KP", "MM", "SY", "AF"]
MEDIUM_RISK_COUNTRIES = ["KH", "PK", "NG", "VE"]
LOW_RISK_COUNTRIES = ["SG", "MY", "ID", "TH", "PH", "VN", "AU", "GB", "US", "JP"]


def _weighted_occupation():
    """Realistic retail-bank mix: most customers are low-risk."""
    low = [o for o in OCCUPATIONS if o[2] == "low"]
    med = [o for o in OCCUPATIONS if o[2] == "medium"]
    high = [o for o in OCCUPATIONS if o[2] == "high"]
    bucket = random.choices(["low", "medium", "high"], weights=[72, 18, 10])[0]
    return random.choice({"low": low, "medium": med, "high": high}[bucket])


def _dob(min_age=21, max_age=75):
    age = random.randint(min_age, max_age)
    base = datetime.now() - timedelta(days=age * 365 + random.randint(0, 364))
    return base.strftime("%Y-%m-%d")


def _make_customer(idx, name=None, residence=None, occ=None,
                   sow=None, doc_verified=True, income=None):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    full = name or f"{first} {last}"
    occupation, industry, occ_risk = occ or _weighted_occupation()
    residence = residence or random.choice(LOW_RISK_COUNTRIES)
    income = income or random.choices(
        [45_000, 80_000, 120_000, 250_000, 600_000],
        weights=[30, 32, 22, 11, 5])[0]
    return {
        "customer_id": f"CUST-{idx:05d}",
        "synthetic": True,
        "full_name": full,
        "date_of_birth": _dob(),
        "nationality": residence,
        "residence_country": residence,
        "occupation": occupation,
        "industry": industry,
        "annual_income_sgd": income,
        "source_of_wealth": sow or random.choice(SOURCE_OF_WEALTH),
        "expected_monthly_volume_sgd": int(income / random.choice([8, 12, 20])),
        "product_requested": random.choice(PRODUCTS),
        "id_document": {
            "type": random.choice(["NRIC", "Passport", "FIN"]),
            "number": f"S{random.randint(1000000,9999999)}X",  # masked-style fake
            "verified": doc_verified,
        },
        "channel": random.choice(["Digital", "Branch", "Relationship Manager"]),
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }


def generate_customers(n=60):
    customers = []
    idx = 1

    # ---- Planted edge cases (so the agent has a story to tell) ----
    # 1) Confirmed sanctions match (exact name + DOB will line up with list)
    sanctioned = _make_customer(idx, name="Viktor Petrov",
                                residence="SY", occ=("Trader", "Trade", "high"))
    sanctioned["date_of_birth"] = "1971-06-15"
    customers.append(sanctioned); idx += 1

    # 2) Near-miss sanctions name (tests false-positive suppression via DOB)
    near = _make_customer(idx, name="Viktor Petroff", residence="SG",
                          occ=("Software Engineer", "Technology", "low"))
    near["date_of_birth"] = "1990-01-01"  # different DOB -> should NOT be a true hit
    customers.append(near); idx += 1

    # 3) PEP
    pep = _make_customer(idx, name="Daniel Reyes", residence="PH",
                         occ=("Civil Servant", "Government", "medium"),
                         income=600_000)
    pep["date_of_birth"] = "1968-09-30"
    customers.append(pep); idx += 1

    # 4) High-risk jurisdiction + high-risk occupation
    customers.append(_make_customer(
        idx, residence="MM",
        occ=("Casino Junket Operator", "Gaming", "high"),
        income=900_000)); idx += 1

    # 5) Adverse media hit
    adverse = _make_customer(idx, name="Marcus Goh", residence="SG",
                             occ=("Crypto Fund Manager", "Virtual Assets", "high"),
                             income=1_200_000)
    customers.append(adverse); idx += 1

    # 6) Incomplete / unverified document -> low confidence -> human review
    customers.append(_make_customer(
        idx, doc_verified=False, sow="Inheritance",
        occ=("Art Dealer", "Art & Antiquities", "high"))); idx += 1

    # ---- Ordinary population ----
    while len(customers) < n:
        customers.append(_make_customer(idx)); idx += 1

    return customers


def generate_sanctions_list():
    """Synthetic stand-in for OFAC SDN / UN / EU consolidated lists."""
    return [
        {"synthetic": True, "list": "UN Consolidated (synthetic)",
         "name": "Viktor Petrov", "dob": "1971-06-15", "country": "SY",
         "program": "Counter-terrorism financing"},
        {"synthetic": True, "list": "OFAC SDN (synthetic)",
         "name": "Olga Ivanova", "dob": "1980-02-20", "country": "RU",
         "program": "Sectoral sanctions"},
        {"synthetic": True, "list": "EU Consolidated (synthetic)",
         "name": "Ahmed Al-Farsi", "dob": "1975-11-05", "country": "SY",
         "program": "Asset freeze"},
    ]


def generate_pep_list():
    """Synthetic Politically Exposed Persons reference data."""
    return [
        {"synthetic": True, "name": "Daniel Reyes", "dob": "1968-09-30",
         "country": "PH", "position": "Deputy Minister of Finance",
         "category": "Senior Government Official"},
        {"synthetic": True, "name": "Grace Suharto", "dob": "1972-04-18",
         "country": "ID", "position": "Provincial Governor",
         "category": "Senior Government Official"},
    ]


def generate_adverse_media():
    """Synthetic adverse-media screening corpus."""
    return [
        {"synthetic": True, "name": "Marcus Goh",
         "headline": "Local crypto fund manager named in market manipulation probe",
         "category": "Financial crime allegation", "severity": "High",
         "source": "synthetic-wire", "date": "2026-02-11"},
        {"synthetic": True, "name": "Kumar Nair",
         "headline": "Businessman cleared after tax dispute settlement",
         "category": "Resolved civil matter", "severity": "Low",
         "source": "synthetic-wire", "date": "2025-08-03"},
    ]


def _write(name, obj):
    path = DATA_DIR / name
    path.write_text(json.dumps(obj, indent=2))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    print(f"  wrote {name:24s} ({len(obj):3d} records)  sha256:{digest}")
    return digest


def main():
    print("Generating synthetic KYC dataset (seed=42, fully reproducible)...")
    customers = generate_customers(60)
    _write("customers.json", customers)
    _write("sanctions_list.json", generate_sanctions_list())
    _write("pep_list.json", generate_pep_list())
    _write("adverse_media.json", generate_adverse_media())
    print("Done. All records flagged synthetic=True (zero PII).")


if __name__ == "__main__":
    main()
