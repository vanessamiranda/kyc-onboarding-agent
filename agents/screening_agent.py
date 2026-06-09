"""
Screening agent: sanctions, PEP, and adverse-media checks.

The interesting engineering here is FALSE-POSITIVE SUPPRESSION. A name-only
match is not a hit — screening systems that escalate every fuzzy name match
drown compliance teams in noise. We require date-of-birth corroboration before
calling a sanctions match "confirmed", and surface name-only matches separately
as "near miss" so a human can see we considered and dismissed them (transparency).
"""

import json
from pathlib import Path

from agents.base import BaseAgent, name_similarity
from governance import feat_mapper

DATA = Path(__file__).parent.parent / "data"
NAME_MATCH_THRESHOLD = 0.85   # tune for precision/recall tradeoff


def _load(fname):
    return json.loads((DATA / fname).read_text())


class ScreeningAgent(BaseAgent):
    name = "ScreeningAgent"

    def __init__(self, audit):
        super().__init__(audit)
        self.sanctions = _load("sanctions_list.json")
        self.peps = _load("pep_list.json")
        self.adverse = _load("adverse_media.json")

    def _screen_sanctions(self, customer):
        best, best_score = None, 0.0
        for entry in self.sanctions:
            s = name_similarity(customer["full_name"], entry["name"])
            if s > best_score:
                best, best_score = entry, s
        if best and best_score >= NAME_MATCH_THRESHOLD:
            dob_match = customer["date_of_birth"] == best["dob"]
            if dob_match:
                return {"hit": True, "near_miss": False,
                        "match": best, "score": best_score}
            # Strong name match, DOB mismatch -> ambiguous near miss
            return {"hit": False, "near_miss": True,
                    "match": best, "score": best_score}
        return {"hit": False, "near_miss": False, "match": None, "score": best_score}

    def _screen_pep(self, customer):
        for entry in self.peps:
            if (name_similarity(customer["full_name"], entry["name"]) >= NAME_MATCH_THRESHOLD
                    and customer["date_of_birth"] == entry["dob"]):
                return {"hit": True, "match": entry}
        return {"hit": False, "match": None}

    def _screen_adverse(self, customer):
        for entry in self.adverse:
            if name_similarity(customer["full_name"], entry["name"]) >= NAME_MATCH_THRESHOLD:
                if entry["severity"] in ("High", "Medium"):
                    return {"hit": True, "match": entry}
        return {"hit": False, "match": None}

    def run(self, context):
        customer = context["customer"]
        result = {
            "sanctions": self._screen_sanctions(customer),
            "pep": self._screen_pep(customer),
            "adverse_media": self._screen_adverse(customer),
        }
        for action in ("sanctions_screening", "pep_screening", "adverse_media_screening"):
            key = action.split("_")[0] if action != "adverse_media_screening" else "adverse_media"
            self.audit.log(
                customer_id=customer["customer_id"],
                agent=self.name,
                action=action,
                inputs={"name": customer["full_name"], "dob": customer["date_of_birth"]},
                output=result[key],
                feat_tags=feat_mapper.tag(action),
            )
        return result
