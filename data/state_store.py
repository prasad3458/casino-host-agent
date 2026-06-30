"""
Runtime state store — ALL writes go here. Source data (guests.py, host_registry.py)
is NEVER modified. This module is the only place that changes at runtime.

In production this would be a database. Here it's an in-memory dict that persists
for the lifetime of the Gradio session.
"""

import copy
from datetime import datetime

# ── In-memory stores (never touch source data) ───────────────────────────────

_approval_queue = []      # pending / decided approval requests
_loaded_offers = []       # offers confirmed loaded to guest accounts
_perf_log = []            # host performance events this session

# ── Approval queue ────────────────────────────────────────────────────────────

def submit_approval_request(host_login: str, guest_id: str, guest_name: str,
                             segment: str, offer_snapshot: dict,
                             reinvestment_pct: float, cap_pct: float,
                             hard_cap_pct: float, reason: str) -> dict:
    """Host submits an over-cap offer for supervisor approval. Returns the request record."""
    req = {
        "id": f"APR-{len(_approval_queue)+1:04d}",
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "host_login": host_login,
        "guest_id": guest_id,
        "guest_name": guest_name,
        "segment": segment,
        "offer": copy.deepcopy(offer_snapshot),   # snapshot — never a reference
        "reinvestment_pct": reinvestment_pct,
        "guest_cap_pct": cap_pct,
        "hard_cap_pct": hard_cap_pct,
        "host_reason": reason,
        "status": "Pending",           # Pending | Approved | Rejected
        "decision_by": None,
        "decision_at": None,
        "decision_note": None,
    }
    _approval_queue.append(req)
    return req

def get_approval_queue(host_login: str = None, supervisor: bool = False) -> list:
    """Return approval requests visible to this user."""
    if supervisor:
        return list(_approval_queue)
    return [r for r in _approval_queue if r["host_login"] == host_login]

def decide_approval(request_id: str, decision: str, decided_by: str, note: str = "") -> bool:
    """Supervisor approves or rejects. Returns True if found."""
    for req in _approval_queue:
        if req["id"] == request_id:
            req["status"] = decision          # "Approved" or "Rejected"
            req["decision_by"] = decided_by
            req["decision_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            req["decision_note"] = note
            return True
    return False

def get_approved_offers(guest_id: str) -> list:
    """Return approved (not yet loaded) offers for a guest."""
    return [r for r in _approval_queue
            if r["guest_id"] == guest_id and r["status"] == "Approved"]

# ── Loaded offers ─────────────────────────────────────────────────────────────

def load_offer_to_account(host_login: str, guest_id: str, guest_name: str,
                           offer_snapshot: dict, channel: str, notes: str = "") -> dict:
    """
    Records that a host has loaded an offer to a guest account.
    This is a WRITE operation on state_store only — source data unchanged.
    """
    record = {
        "id": f"OFR-{len(_loaded_offers)+1:04d}",
        "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "host_login": host_login,
        "guest_id": guest_id,
        "guest_name": guest_name,
        "offer": copy.deepcopy(offer_snapshot),
        "channel": channel,
        "notes": notes,
        "status": "Active",      # Active | Redeemed | Expired
    }
    _loaded_offers.append(record)
    return record

def get_loaded_offers(host_login: str = None, guest_id: str = None) -> list:
    results = _loaded_offers
    if host_login:
        results = [r for r in results if r["host_login"] == host_login]
    if guest_id:
        results = [r for r in results if r["guest_id"] == guest_id]
    return results

# ── Performance log ───────────────────────────────────────────────────────────

def log_perf_event(host_login: str, event_type: str, guest_id: str,
                   amount: float, notes: str = ""):
    """Log a performance-relevant event (offer loaded, comp cost, etc.)."""
    _perf_log.append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "host_login": host_login,
        "event_type": event_type,
        "guest_id": guest_id,
        "amount": amount,
        "notes": notes,
    })

def get_perf_log(host_login: str = None) -> list:
    if host_login:
        return [e for e in _perf_log if e["host_login"] == host_login]
    return list(_perf_log)

# ── Clear session (never clears source data) ─────────────────────────────────

def reset_session_state():
    """For demo reset only. Does NOT touch guests.py or host_registry.py."""
    global _approval_queue, _loaded_offers, _perf_log
    _approval_queue = []
    _loaded_offers = []
    _perf_log = []
