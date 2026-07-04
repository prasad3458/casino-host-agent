"""
Runtime state store — ALL writes go here. Source data (guests.py, host_registry.py)
is NEVER modified at runtime. This module is the only place that changes during
a live session.

Design:
  - _approval_queue  : pending / decided supervisor approval requests
  - _loaded_offers   : offers confirmed loaded to guest accounts
  - _perf_log        : host performance events for this session

Offer snapshots stored here use copy.deepcopy() so no reference can accidentally
mutate source data. Offer snapshots from the refinement pipeline also carry a
_guest_id key (set by refine_offer() in app.py) which the Chat, Outreach, and
Load functions use to verify an offer actually belongs to the selected guest
before trusting it — preventing cross-guest contamination when the host switches
guests mid-session without re-analyzing.

In production this would be backed by a database (Cloud Firestore, BigQuery, or
similar). Here it is an in-memory store that persists for the lifetime of the
Gradio server process.
"""

import copy
from datetime import datetime

# ── In-memory stores ──────────────────────────────────────────────────────────
# These are module-level lists — shared across all Gradio sessions on the same
# server process. In a multi-user production deployment, these would be replaced
# by per-user database records. For this demo, a single host per session is the
# expected usage pattern.

_approval_queue: list = []   # pending / decided approval requests
_loaded_offers:  list = []   # offers confirmed loaded to guest accounts
_perf_log:       list = []   # host performance events this session


# ── Approval queue ────────────────────────────────────────────────────────────

def submit_approval_request(host_login: str, guest_id: str, guest_name: str,
                             segment: str, offer_snapshot: dict,
                             reinvestment_pct: float, cap_pct: float,
                             hard_cap_pct: float, reason: str) -> dict:
    """
    Submit an over-cap offer for supervisor approval.

    Called by app.py when a host attempts to load an offer whose reinvestment
    rate falls between the guest's personal cap and the segment's hard cap.
    Offers above the hard cap are blocked outright and never reach this function.

    The offer_snapshot is deep-copied so future refinements or resets cannot
    alter what was actually submitted for review.

    Returns the full request record including the generated APR-XXXX ID.
    """
    req = {
        "id":               f"APR-{len(_approval_queue) + 1:04d}",
        "submitted_at":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        "host_login":       host_login,
        "guest_id":         guest_id,
        "guest_name":       guest_name,
        "segment":          segment,
        "offer":            copy.deepcopy(offer_snapshot),  # snapshot, never a reference
        "reinvestment_pct": reinvestment_pct,
        "guest_cap_pct":    cap_pct,
        "hard_cap_pct":     hard_cap_pct,
        "host_reason":      reason,
        "status":           "Pending",    # Pending | Approved | Rejected
        "decision_by":      None,
        "decision_at":      None,
        "decision_note":    None,
    }
    _approval_queue.append(req)
    return req


def get_approval_queue(host_login: str = None, supervisor: bool = False) -> list:
    """
    Return approval requests visible to this user.

    Supervisors see all requests across all hosts.
    Regular hosts see only their own submissions.
    """
    if supervisor:
        return list(_approval_queue)
    return [r for r in _approval_queue if r["host_login"] == host_login]


def decide_approval(request_id: str, decision: str,
                    decided_by: str, note: str = "") -> bool:
    """
    Supervisor approves or rejects a pending request.

    decision must be "Approved" or "Rejected".
    Returns True if the request was found and updated, False if not found.
    After approval, the caller (app.py) is responsible for calling
    load_offer_to_account() to actually commit the offer.
    """
    for req in _approval_queue:
        if req["id"] == request_id:
            req["status"]        = decision
            req["decision_by"]   = decided_by
            req["decision_at"]   = datetime.now().strftime("%Y-%m-%d %H:%M")
            req["decision_note"] = note
            return True
    return False


def get_approved_offers(guest_id: str) -> list:
    """Return all approved (not yet expired) offers for a specific guest."""
    return [r for r in _approval_queue
            if r["guest_id"] == guest_id and r["status"] == "Approved"]


# ── Loaded offers ─────────────────────────────────────────────────────────────

def load_offer_to_account(host_login: str, guest_id: str, guest_name: str,
                           offer_snapshot: dict, channel: str,
                           notes: str = "") -> dict:
    """
    Record that a host has loaded a finalized offer to a guest account.

    This is the authoritative "what was actually sent to this guest" record.
    The Host AI Chat reads this via get_loaded_offers() when answering questions
    like "what's the last offer loaded" — so it reflects the real committed
    offer rather than whatever the engine would derive fresh from defaults.

    The offer_snapshot is deep-copied so post-load refinements cannot
    retroactively alter what was recorded as sent.

    Status values: Active | Redeemed | Expired
    Returns the full record including the generated OFR-XXXX ID.
    """
    record = {
        "id":         f"OFR-{len(_loaded_offers) + 1:04d}",
        "loaded_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        "host_login": host_login,
        "guest_id":   guest_id,
        "guest_name": guest_name,
        "offer":      copy.deepcopy(offer_snapshot),
        "channel":    channel,
        "notes":      notes,
        "status":     "Active",   # Active | Redeemed | Expired
    }
    _loaded_offers.append(record)
    return record


def get_loaded_offers(host_login: str = None, guest_id: str = None) -> list:
    """
    Return loaded offer records, optionally filtered by host and/or guest.

    Called by:
      - app.py chat_respond()   — to find the most recently committed offer
                                  for a guest when no live refinement exists
      - app.py build_portfolio_context()  — for the portfolio chat summary
      - app.py render_perf_dashboard()    — for session offer count
    """
    results = list(_loaded_offers)
    if host_login:
        results = [r for r in results if r["host_login"] == host_login]
    if guest_id:
        results = [r for r in results if r["guest_id"] == guest_id]
    return results


# ── Performance log ───────────────────────────────────────────────────────────

def log_perf_event(host_login: str, event_type: str, guest_id: str,
                   amount: float, notes: str = "") -> None:
    """
    Log a performance-relevant event for the current session.

    event_type examples: "offer_loaded", "comp_cost", "approval_submitted"
    In production this would write to an analytics pipeline (BigQuery, etc.)
    and feed into the host's YTD performance metrics in real time.
    Here it is used to track offer activity within the Gradio session.
    """
    _perf_log.append({
        "ts":          datetime.now().strftime("%Y-%m-%d %H:%M"),
        "host_login":  host_login,
        "event_type":  event_type,
        "guest_id":    guest_id,
        "amount":      amount,
        "notes":       notes,
    })


def get_perf_log(host_login: str = None) -> list:
    """Return performance log entries, optionally filtered by host."""
    if host_login:
        return [e for e in _perf_log if e["host_login"] == host_login]
    return list(_perf_log)


# ── Session reset (demo utility) ─────────────────────────────────────────────

def reset_session_state() -> None:
    """
    Clear all runtime state for a fresh demo session.

    This ONLY clears the in-memory stores above.
    It does NOT touch guests.py, host_registry.py, or any source data.
    Safe to call between test runs without affecting the base data.
    """
    global _approval_queue, _loaded_offers, _perf_log
    _approval_queue = []
    _loaded_offers  = []
    _perf_log       = []
