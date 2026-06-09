"""
Tamper-evident audit trail.

WHY A HASH CHAIN
----------------
A regulator's first question about any AI decision is "prove what happened, and
prove the log wasn't edited after the fact." We chain each entry's hash into the
next (like a mini-blockchain / git history). If anyone alters an earlier entry,
every subsequent hash breaks and `verify_integrity()` returns False. This is the
single most important thing that turns an "AI demo" into something a bank's
second line of defence (compliance) will take seriously.
"""

import json
import hashlib
from datetime import datetime, timezone


class AuditTrail:
    def __init__(self):
        self._entries = []
        self._genesis = "0" * 64  # genesis hash, like the first block

    def _prev_hash(self):
        return self._entries[-1]["entry_hash"] if self._entries else self._genesis

    @staticmethod
    def _hash(payload: dict) -> str:
        # Deterministic serialisation so the hash is reproducible
        blob = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(blob).hexdigest()

    def log(self, *, customer_id, agent, action, inputs, output,
            feat_tags, confidence=None, human_review=False):
        """Append one immutable, hash-chained event."""
        entry_core = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "customer_id": customer_id,
            "agent": agent,
            "action": action,
            "inputs_digest": self._hash(inputs)[:16],  # store digest, not raw PII
            "output": output,
            "feat_tags": feat_tags,
            "confidence": confidence,
            "human_review_required": human_review,
            "prev_hash": self._prev_hash(),
        }
        entry_core["entry_hash"] = self._hash(entry_core)
        self._entries.append(entry_core)
        return entry_core

    def verify_integrity(self) -> bool:
        """Re-walk the chain; returns False if any entry was tampered with."""
        prev = self._genesis
        for e in self._entries:
            recomputed = dict(e)
            stored = recomputed.pop("entry_hash")
            if recomputed["prev_hash"] != prev:
                return False
            if self._hash(recomputed) != stored:
                return False
            prev = stored
        return True

    def for_customer(self, customer_id):
        return [e for e in self._entries if e["customer_id"] == customer_id]

    def export(self):
        return {
            "audit_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "integrity_verified": self.verify_integrity(),
            "entry_count": len(self._entries),
            "entries": self._entries,
        }
