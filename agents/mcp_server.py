"""
Casino Host MCP Server
======================
Exposes guest data, offer catalog, guardrail rules, and offer history as
Model Context Protocol (MCP) tools that any MCP-compatible client or agent
can call — including the ADK orchestrator in this project.

Design:
  - READ-ONLY: all tools return data, none mutate source files
  - Scoped by host_login: tools refuse to return another host's guests
  - FastMCP transport: runs as a subprocess the ADK MCPToolset connects to

Usage (standalone):
    python agents/mcp_server.py

Usage (from ADK agent via MCPToolset):
    See agents/adk_agents.py — MCPToolset(server_params=StdioServerParameters(...))

Tools exposed:
    get_guest_profile       — full guest dict for one guest (host-scoped)
    get_guest_list          — priority-ranked list for a host's portfolio
    get_offer_catalog       — full offer catalog (rooms, food, gaming, shows, spa)
    get_guardrails          — guardrail rules and thresholds
    get_offer_history       — past accepted/declined offers for a guest
    score_guest_propensity  — compute propensity score + quadrant
    compute_guest_analytics — trip analytics (avg gap, overdue days, trend)
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from data.guests import GUESTS, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY
from data.host_registry import HOSTS, APPROVAL_THRESHOLDS
from agents.engine import compute_trip_analytics, score_propensity, analyze_offer_history

# ── Server init ───────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="casino-host-agent",
    instructions="Tools for casino host guest management, offer construction, and reinvestment analysis",
)

# ── Security helper ───────────────────────────────────────────────────────────
def _is_authorized(host_login: str, guest: dict) -> bool:
    """
    Enforce host-level access control.
    Supervisors may access all guests. Hosts may only access their own portfolio.
    """
    h = HOSTS.get(host_login, {})
    if h.get("supervisor"):
        return True
    return guest.get("host") == h.get("display_name", "")


# ── Tool: get_guest_profile ───────────────────────────────────────────────────
@mcp.tool()
def get_guest_profile(guest_id: str, host_login: str) -> str:
    """
    Retrieve the full profile for a single guest.

    Args:
        guest_id:   Guest identifier (e.g. 'G001')
        host_login: Authenticated host username (e.g. 'maria.santos')

    Returns:
        JSON string with guest profile, or error message if not authorized.

    Security:
        Returns 403-style error if host_login does not own this guest.
        Source data is returned read-only — no mutation occurs.
    """
    guest = next((g for g in GUESTS if g["id"] == guest_id), None)
    if not guest:
        return json.dumps({"error": f"Guest {guest_id} not found"})
    if not _is_authorized(host_login, guest):
        return json.dumps({"error": "Access denied — this guest is not in your portfolio"})

    # Return a safe copy without mutating source
    safe = {k: v for k, v in guest.items() if k != "trips"}
    safe["trip_count"] = len(guest.get("trips", []))
    safe["last_3_trips"] = guest.get("trips", [])[-3:]
    return json.dumps(safe, default=str)


# ── Tool: get_guest_list ──────────────────────────────────────────────────────
@mcp.tool()
def get_guest_list(host_login: str) -> str:
    """
    Return priority-ranked guest list for the authenticated host's portfolio.

    Guests are ranked by: days overdue × propensity score × avg trip value.
    Lapsed guests (90+ days overdue) appear first.

    Args:
        host_login: Authenticated host username

    Returns:
        JSON array of guest summaries with propensity and visit status.
    """
    h = HOSTS.get(host_login, {})
    if not h:
        return json.dumps({"error": "Unknown host login"})

    if h.get("supervisor"):
        my_guests = GUESTS
    else:
        dn = h.get("display_name", "")
        my_guests = [g for g in GUESTS if g.get("host") == dn]

    results = []
    for g in my_guests:
        a = compute_trip_analytics(g)
        p = score_propensity(g, a, OFFER_HISTORY)
        oh = analyze_offer_history(g, OFFER_HISTORY)
        results.append({
            "id": g["id"],
            "name": g["name"],
            "segment": g["segment"],
            "tier": g["tier"],
            "days_overdue": a["days_overdue"],
            "propensity_score": p["score"],
            "quadrant": p["quadrant"],
            "avg_trip_value": a["avg_total_trip_value"],
            "offer_accept_rate": oh.get("accept_rate", 0),
            "n_past_offers": oh.get("n_offers", 0),
            "best_channel": oh.get("best_channel", g["contact_pref"][0]),
            "expected_return": a["expected_return_date"],
        })

    # Sort: most overdue first, then propensity × value descending
    results.sort(key=lambda x: (
        -max(0, x["days_overdue"]),
        -(x["propensity_score"] * x["avg_trip_value"])
    ))
    return json.dumps(results)


# ── Tool: get_offer_catalog ───────────────────────────────────────────────────
@mcp.tool()
def get_offer_catalog(segment: str = "") -> str:
    """
    Return the full offer catalog, optionally filtered to a guest segment.

    Args:
        segment: Optional filter — one of: Developing, Mid-tier, Premium,
                 High Roller, Whale. Leave empty for full catalog.

    Returns:
        JSON object with rooms, food_comps, gaming_comps, shows, spa —
        each filtered to eligible entries for the given segment.
    """
    if not segment:
        return json.dumps(OFFER_CATALOG)

    filtered = {}
    for category, items in OFFER_CATALOG.items():
        filtered[category] = {
            name: info for name, info in items.items()
            if segment in info.get("eligible_segments", [])
        }
    return json.dumps(filtered)


# ── Tool: get_guardrails ──────────────────────────────────────────────────────
@mcp.tool()
def get_guardrails(segment: str = "") -> str:
    """
    Return guardrail rules and approval thresholds.

    Args:
        segment: Optional segment to return specific thresholds for.

    Returns:
        JSON with global guardrails + approval thresholds for the segment.
    """
    result = dict(GUARDRAILS)
    if segment and segment in APPROVAL_THRESHOLDS:
        result["approval_thresholds"] = APPROVAL_THRESHOLDS[segment]
    elif not segment:
        result["approval_thresholds"] = APPROVAL_THRESHOLDS
    return json.dumps(result)


# ── Tool: get_offer_history ───────────────────────────────────────────────────
@mcp.tool()
def get_offer_history(guest_id: str, host_login: str) -> str:
    """
    Return the past offer history for a guest — accepted and declined.

    This is the key input for the acceptance model: the agent uses decline
    reasons and accepted offer patterns to determine must-have components
    and the minimum gaming threshold for acceptance.

    Args:
        guest_id:   Guest identifier
        host_login: Authenticated host (enforces access control)

    Returns:
        JSON with history records + derived insights (must-haves, min gaming,
        channel rates, accept rate).
    """
    guest = next((g for g in GUESTS if g["id"] == guest_id), None)
    if not guest:
        return json.dumps({"error": f"Guest {guest_id} not found"})
    if not _is_authorized(host_login, guest):
        return json.dumps({"error": "Access denied"})

    history = OFFER_HISTORY.get(guest_id, [])
    oh = analyze_offer_history(guest, OFFER_HISTORY)

    return json.dumps({
        "history": history,
        "insights": oh,
    }, default=str)


# ── Tool: score_guest_propensity ──────────────────────────────────────────────
@mcp.tool()
def score_guest_propensity(guest_id: str, host_login: str) -> str:
    """
    Compute the propensity score (0–100) and 2×2 quadrant for a guest.

    The score blends:
      - Recency (days overdue relative to personal cadence)
      - Frequency (total trips)
      - Gaming trend (recent vs earlier trips)
      - Segment bonus
      - Historical offer acceptance rate

    Args:
        guest_id:   Guest identifier
        host_login: Authenticated host

    Returns:
        JSON with score, value_bucket, propensity_bucket, quadrant, and
        the analytics that drove the score.
    """
    guest = next((g for g in GUESTS if g["id"] == guest_id), None)
    if not guest:
        return json.dumps({"error": f"Guest {guest_id} not found"})
    if not _is_authorized(host_login, guest):
        return json.dumps({"error": "Access denied"})

    analytics  = compute_trip_analytics(guest)
    propensity = score_propensity(guest, analytics, OFFER_HISTORY)
    return json.dumps({"propensity": propensity, "analytics": analytics})


# ── Tool: compute_guest_analytics ─────────────────────────────────────────────
@mcp.tool()
def compute_guest_analytics(guest_id: str, host_login: str) -> str:
    """
    Return detailed trip analytics for a guest.

    Analytics include: avg days between visits, days since last visit,
    days overdue relative to personal cadence, avg gaming loss per trip,
    avg total trip value, gaming trend (% change recent vs earlier trips),
    and expected return date.

    Args:
        guest_id:   Guest identifier
        host_login: Authenticated host

    Returns:
        JSON analytics dict.
    """
    guest = next((g for g in GUESTS if g["id"] == guest_id), None)
    if not guest:
        return json.dumps({"error": f"Guest {guest_id} not found"})
    if not _is_authorized(host_login, guest):
        return json.dumps({"error": "Access denied"})

    return json.dumps(compute_trip_analytics(guest))


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Run as stdio MCP server — ADK MCPToolset will spawn this as a subprocess
    mcp.run(transport="stdio")
