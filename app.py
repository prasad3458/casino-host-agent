"""
Kaggle Resort — Host Intelligence Agent
New: Interactive offer refinement · Offer history display · AI rationale one-liner
     History-aware acceptance probability · Per-component rationale panel
     Live model selector — switch between Gemini models mid-session
"""

import os, sys, copy, re
from datetime import date, datetime
import gradio as gr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.guests import GUESTS, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY
from data.host_registry import HOSTS, HOST_NAME_TO_KEY, APPROVAL_THRESHOLDS
from data.state_store import (
    submit_approval_request, get_approval_queue, decide_approval,
    load_offer_to_account, get_loaded_offers, log_perf_event,
)
from agents.engine import (
    analyze_guest, get_due_guests, compute_trip_analytics, score_propensity,
    simulate_roi, build_offer, apply_offer_adjustments, analyze_offer_history,
)
from agents.gemini_agent import (
    get_model, get_initial_brief, generate_offer_rationale,
    explain_refinement, chat_with_host, generate_outreach_content, build_context_prompt,
    _extract_text, parse_refinement_with_llm,
    build_portfolio_context_prompt, chat_about_portfolio,
)

# ── Available models ──────────────────────────────────────────────────────────
# The three best free-tier models from the user's Google AI Studio plan.
# RPD = requests per day on free tier.
AVAILABLE_MODELS = {
    "gemini-2.5-flash":       "Gemini 2.5 Flash  — Best prose quality  (20 RPD free)",
    "gemini-3.1-flash-lite":  "Gemini 3.1 Flash Lite — Fastest + smartest benchmarks  (500 RPD free)",
    "gemini-3.5-flash":       "Gemini 3.5 Flash  — Newest 3.5 series  (20 RPD free)",
}
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MODEL_CHOICES  = list(AVAILABLE_MODELS.keys())
MODEL_LABELS   = [f"{k}  ·  {v.split('—')[1].strip()}" for k, v in AVAILABLE_MODELS.items()]

# ── Gemini client factory (model-aware, not a singleton) ──────────────────────
def get_gemini_for_model(model_id: str):
    """
    Return a live Gemini client configured for model_id.
    Called per-request so the host can switch models at any time.
    Returns None if GEMINI_API_KEY is not set (app runs in analytics-only mode).
    """
    return get_model(model_id)

# ── Auth / access ─────────────────────────────────────────────────────────────
def authenticate(username, password):
    u = username.strip().lower()
    h = HOSTS.get(u)
    if not h or h["password"] != password.strip():
        return None, "Invalid username or password."
    return u, None

def get_my_guests(host_login):
    h = HOSTS.get(host_login, {})
    if h.get("supervisor"):
        return GUESTS
    dn = h.get("display_name", "")
    return [g for g in GUESTS if g.get("host") == dn]

# ── Guardrail check ───────────────────────────────────────────────────────────
def check_guardrails_full(guest, offer_cost, reinvest_pct):
    segment = guest["segment"]
    cap_pct = guest["reinvestment_cap_pct"] * 100
    thresh  = APPROVAL_THRESHOLDS.get(segment, {})
    soft    = thresh.get("soft_cap_pct", cap_pct / 100) * 100
    hard    = thresh.get("hard_cap_pct", 0.45) * 100
    seg_cap = GUARDRAILS["max_total_offer_cost"][segment]
    if offer_cost > seg_cap:
        return "hard_block", f"Exceeds segment cost cap ${seg_cap:,}"
    if reinvest_pct > hard:
        return "hard_block", f"Exceeds hard cap {hard:.0f}% — supervisor override required"
    if reinvest_pct > soft:
        return "needs_approval", f"Above guest cap {soft:.0f}% — submit for supervisor approval"
    return "ok", "Within guardrails ✅"

# ── Performance dashboard ─────────────────────────────────────────────────────
def build_performance(host_login):
    my = get_my_guests(host_login)
    hi = HOSTS.get(host_login, {})
    target = hi.get("ytd_revenue_target") or 0
    ytd_rev = ytd_cost = ytd_trips = py_rev = py_cost = py_trips = 0
    for g in my:
        for t in g.get("ytd_trips_2026", []):
            ytd_rev   += abs(t.get("gaming_win_loss", 0)) + t.get("food_spend", 0) + t.get("show_spend", 0) + t.get("spa_spend", 0)
            ytd_cost  += t.get("comp_cost", 0); ytd_trips += 1
        for t in g.get("ytd_trips_2025", []):
            py_rev    += abs(t.get("gaming_win_loss", 0)) + t.get("food_spend", 0) + t.get("show_spend", 0) + t.get("spa_spend", 0)
            py_cost   += t.get("comp_cost", 0); py_trips  += 1
    ytd_ri = round(ytd_cost / ytd_rev * 100, 1) if ytd_rev > 0 else 0
    py_ri  = round(py_cost  / py_rev  * 100, 1) if py_rev  > 0 else 0
    remaining   = max(0, target - ytd_rev)
    pct_target  = round(ytd_rev / target * 100, 1) if target > 0 else 0
    yoy         = round((ytd_rev - py_rev) / py_rev * 100, 1) if py_rev > 0 else 0
    return {
        "ytd_rev": ytd_rev, "ytd_cost": ytd_cost, "ytd_trips": ytd_trips, "ytd_ri": ytd_ri,
        "py_rev": py_rev,   "py_cost": py_cost,   "py_trips": py_trips,   "py_ri":  py_ri,
        "target": target, "remaining": remaining, "pct_target": pct_target, "yoy": yoy,
        "active_guests": len(my),
        "loaded":  len(get_loaded_offers(host_login=host_login)),
        "pending": len([r for r in get_approval_queue(host_login=host_login) if r["status"] == "Pending"]),
    }

def render_perf_dashboard(host_login):
    if not host_login: return "_Log in to view._"
    p   = build_performance(host_login)
    arr = "▲" if p["yoy"] >= 0 else "▼"
    bar = "█" * min(int(p["pct_target"] / 5), 20) + "░" * max(0, 20 - int(p["pct_target"] / 5))
    return f"""## 📊 My Performance — {date.today().strftime("%B %d, %Y")}

### YTD 2026 vs FY 2025
| Metric | YTD 2026 | FY 2025 | Change |
|--------|----------|---------|--------|
| Revenue Generated | **${p['ytd_rev']:,}** | ${p['py_rev']:,} | {arr} {abs(p['yoy'])}% |
| Comp Cost | ${p['ytd_cost']:,} | ${p['py_cost']:,} | — |
| Reinvestment Rate | {p['ytd_ri']}% | {p['py_ri']}% | — |
| Guest Trips Activated | {p['ytd_trips']} | {p['py_trips']} | — |

### Target Progress
`{bar}` **{p['pct_target']}%** of ${p['target']:,} annual goal
Revenue to go: **${p['remaining']:,}**

### Portfolio
Active guests: **{p['active_guests']}** · Offers loaded this session: {p['loaded']} · Pending approvals: {'⚠️ ' + str(p['pending']) if p['pending'] else '0'}
"""

# ── Guest list ────────────────────────────────────────────────────────────────
def render_guest_list(host_login):
    if not host_login: return []
    due = get_due_guests(get_my_guests(host_login), OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)
    rows = []
    for d in due:
        status = "🔴 LAPSED" if d["days_overdue"] > 90 else ("🟡 OVERDUE" if d["days_overdue"] > 0 else "🟢 UPCOMING")
        ov_str = f"+{d['days_overdue']}d" if d["days_overdue"] > 0 else f"in {-d['days_overdue']}d"
        loaded = "📋 Loaded" if get_loaded_offers(host_login=host_login, guest_id=d["id"]) else ""
        oh     = analyze_offer_history(next(g for g in GUESTS if g["id"] == d["id"]), OFFER_HISTORY)
        rows.append([status, d["name"], d["segment"], d["tier"],
                     f"${d['avg_trip_value']:,}", f"{d['propensity_score']}/100",
                     ov_str, d["primary_contact"],
                     f"{oh['accept_rate']}% ({oh['n_offers']} offers)" if oh["n_offers"] else "No history",
                     loaded])
    return rows

GL_HEADERS = ["Status", "Guest", "Segment", "Tier", "Avg Trip", "Propensity",
              "Visit Status", "Best Contact", "Offer History", "Loaded"]

# ── Core analysis (model-aware) ───────────────────────────────────────────────
def run_analysis(guest_name, host_login, model_id):
    if not host_login:
        return ("_Log in first._",) * 5 + ("", "", "", "", [], "", "")
    my    = get_my_guests(host_login)
    guest = next((g for g in my if g["name"] == guest_name), None)
    if not guest:
        return ("⛔ Access denied — not your guest.",) + ("",) * 4 + ("", "", "", "", [], "", "")

    analysis = analyze_guest(guest, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)
    client   = get_gemini_for_model(model_id)
    g, a, p, o, s, c = (analysis[k] for k in ["guest", "analytics", "propensity", "offer", "simulation", "contact"])
    oh = o.get("offer_history_summary", {})

    profile_md = f"""### {g['name']}
**Segment:** {g['segment']} · **Tier:** {g['tier']} · **Host:** {g.get('host', '—')}
**Location:** {g['city']} · **Age:** {g['age']} · **Contact:** {', '.join(g['contact_pref'])}
> {g.get('notes', '')}
"""
    trip_rows = []
    for t in sorted(g["trips"], key=lambda x: x["date"], reverse=True)[:8]:
        pl = t["gaming_win_loss"]
        trip_rows.append([t["date"], t["room"], f"{t['nights']}N",
                          f"{'▲' if pl > 0 else '▼'} ${abs(pl):,}",
                          f"${t['food_spend']:,}", f"${t['show_spend']:,}", f"${t['spa_spend']:,}",
                          ", ".join(t.get("offers_redeemed", []))])

    offer_hist_rows = []
    for h in reversed(OFFER_HISTORY.get(g["id"], [])):
        icon   = "✅" if h["outcome"] == "Accepted" else "❌"
        o_items = [v for k, v in h["offer"].items() if v and k not in ("total",) and isinstance(v, str)]
        offer_hist_rows.append([
            h["date"], f"{icon} {h['outcome']}", h.get("channel", "—"),
            ", ".join(o_items[:4]), f"${h['offer'].get('total', 0):,}",
            h.get("notes", "")[:90],
        ])

    _, gr_msg = check_guardrails_full(g, o["total_offer_cost"], o["reinvestment_pct"])
    offer_lines = []
    for key, icon, label in [("room","🛏","Room"), ("food_comp","🍽","F&B"),
                              ("gaming_comp","🎰","Gaming"), ("show","🎭","Show"), ("spa","🧖","Spa")]:
        item = o[key]
        if item.get("name"):
            nights_s = f" × {o['room']['nights']}N" if key == "room" else ""
            offer_lines.append(f"| {icon} {label} | {item['name']}{nights_s} | ${item.get('cost', 0):,} |")

    missing_warn = ""
    if s.get("missing_must_haves"):
        missing_warn = f"\n⚠️ **Missing must-haves:** {', '.join(s['missing_must_haves'])} — acceptance probability reduced."
    hist_md = ""
    if oh.get("n_offers"):
        hist_md = (f"\n**Past offer acceptance:** {oh['accept_rate']}% ({oh['n_accepted']}/{oh['n_offers']} offers) · "
                   f"Best channel: **{oh.get('best_channel', 'N/A')}** · "
                   f"Min gaming that converted: **${oh.get('min_gaming_accepted', 0):,}**")

    offer_md = f"""### Recommended Offer
| Category | Component | Cost |
|----------|-----------|------|
{chr(10).join(offer_lines)}
| | **TOTAL** | **${o['total_offer_cost']:,}** |

**Reinvestment:** {o['reinvestment_pct']}% (cap: {int(g['reinvestment_cap_pct']*100)}%) · {gr_msg}
**Acceptance probability:** {s['accept_probability_pct']}% _(history-adjusted)_
**Expected net:** ${s['expected_net_if_visit']:,} · ROI: {s['roi_ratio']}x{missing_warn}{hist_md}
"""
    rat = o.get("rationale", {})
    rat_lines = [f"**{k.title()}:** {v}" for k, v in rat.items()
                 if k != "_summary" and v]
    rat_md = "### Why This Offer?\n" + "\n\n".join(rat_lines)
    if rat.get("_summary"):
        rat_md += f"\n\n---\n_{rat['_summary']}_"

    ai_rationale = generate_offer_rationale(analysis, client)
    brief        = get_initial_brief(analysis, client)

    return (profile_md, offer_md, rat_md, ai_rationale, brief,
            guest_name, str(o), g["id"], g["segment"],
            trip_rows, offer_hist_rows, gr_msg)

# ── Offer refinement (model-aware, chains from previous refinement) ──────────
def refine_offer(instruction, guest_name, host_login, model_id, prior_offer):
    """
    Apply a refinement instruction. If prior_offer is a valid offer dict AND
    belongs to THIS SAME guest (checked via the _guest_id tag), the new
    instruction is applied ON TOP of it — so successive refinements compound
    instead of resetting to the original default offer every time.

    If the host switched guests since the last refinement, prior_offer would
    belong to a DIFFERENT guest — in that case we correctly ignore it and start
    fresh from this guest's default offer, rather than carrying over numbers
    that have no relationship to the newly-selected guest.
    """
    if not host_login:  return "Log in first.", "", "", "", {}
    if not guest_name:  return "Analyze a guest first.", "", "", "", {}
    my    = get_my_guests(host_login)
    guest = next((g for g in my if g["name"] == guest_name), None)
    if not guest: return "⛔ Access denied.", "", "", "", {}

    analytics  = compute_trip_analytics(guest)
    propensity = score_propensity(guest, analytics, OFFER_HISTORY)

    # Chain from the prior refined offer ONLY if it belongs to this same guest
    prior_belongs_to_this_guest = (
        prior_offer and isinstance(prior_offer, dict)
        and prior_offer.get("total_offer_cost")
        and prior_offer.get("_guest_id") == guest["id"]
    )
    if prior_belongs_to_this_guest:
        old_offer = prior_offer
    else:
        old_offer = build_offer(guest, analytics, propensity, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)

    client = get_gemini_for_model(model_id)

    # Step 1: LLM reads the natural-language instruction + current offer + guest
    # history and returns a structured plan (which component to change, by how
    # much, or a target total). This is the actual "understanding" step — no
    # keyword matching, the LLM interprets intent, vague phrasing, and tradeoffs.
    # If the live API call fails for any reason, this transparently falls back
    # to a regex parser that ALSO checks total-language first (see _fallback_regex_parse).
    offer_history_summary = old_offer.get("offer_history_summary", {})
    llm_overrides = parse_refinement_with_llm(
        instruction, old_offer, guest, OFFER_CATALOG, offer_history_summary, client
    )

    # RAW DEBUG SNAPSHOT — captured immediately after parsing, before any further
    # processing can alter it. This shows EXACTLY what came back, with no risk of
    # later steps having silently transformed it.
    raw_debug = (f"client={'LIVE' if client is not None else 'NONE (no API key)'} | "
                f"llm_overrides={dict(llm_overrides)}")

    # Step 2: the engine deterministically EXECUTES that plan against the real
    # catalog and guardrails — this is what keeps every dollar amount traceable
    # and prevents the LLM from inventing prices that don't exist in the catalog.
    new_offer = apply_offer_adjustments(llm_overrides, old_offer, guest, analytics, propensity,
                                          OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)

    # Tag the offer with this guest's ID so downstream consumers (Outreach, Load,
    # and the next refinement call) can verify it actually belongs to this guest
    # before trusting it, rather than silently applying a stale offer to the wrong person.
    new_offer["_guest_id"] = guest["id"]

    explanation = explain_refinement(instruction, old_offer, new_offer,
                                      analyze_guest(guest, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY), client)

    # Surface how the LLM interpreted an ambiguous request, if it told us
    llm_note = llm_overrides.get("_llm_reasoning", "")
    if llm_note:
        explanation = f"_How I interpreted this: {llm_note}_\n\n{explanation}"

    # Lightweight diagnostic — visible only if old/new totals are suspiciously identical
    # despite a non-trivial instruction, which usually means parsing silently no-opped.
    if old_offer.get("total_offer_cost") == new_offer.get("total_offer_cost") and len(instruction.strip()) > 15:
        explanation += (f"\n\n_⚠️ Note: the total didn't change ({new_offer['total_offer_cost']:,}). "
                        f"If you expected a change, try being more specific "
                        f"(e.g. 'set gaming to $5000' or 'increase total to $6500')._")

    # VERSION FINGERPRINT — always visible, proves which code build is actually running.
    # If this string does NOT appear in your live app, the Space is serving stale code.
    explanation += f"\n\n---\n🏷️ `engine-build: 2026-06-30-totalfix-v3`\n🔬 `{raw_debug}`"

    _, gr_msg = check_guardrails_full(guest, new_offer["total_offer_cost"], new_offer["reinvestment_pct"])
    offer_lines = []
    for key, icon, label in [("room","🛏","Room"), ("food_comp","🍽","F&B"),
                              ("gaming_comp","🎰","Gaming"), ("show","🎭","Show"), ("spa","🧖","Spa")]:
        item = new_offer[key]
        if item.get("name"):
            nights_s = f" × {new_offer['room']['nights']}N" if key == "room" else ""
            offer_lines.append(f"| {icon} {label} | {item['name']}{nights_s} | ${item.get('cost', 0):,} |")

    sim = simulate_roi(guest, new_offer, propensity, analytics, OFFER_HISTORY)
    missing_warn = (f"\n⚠️ **Missing must-haves:** {', '.join(sim['missing_must_haves'])} — acceptance reduced."
                    if sim.get("missing_must_haves") else "")

    new_offer_md = f"""### Revised Offer
| Category | Component | Cost |
|----------|-----------|------|
{chr(10).join(offer_lines)}
| | **TOTAL** | **${new_offer['total_offer_cost']:,}** |

**Reinvestment:** {new_offer['reinvestment_pct']}% (cap: {int(guest['reinvestment_cap_pct']*100)}%) · {gr_msg}
**Acceptance probability:** {sim['accept_probability_pct']}% · **Net:** ${sim['expected_net_if_visit']:,} · **ROI:** {sim['roi_ratio']}x{missing_warn}
"""
    rat     = new_offer.get("rationale", {})
    rat_md  = "### Revised Rationale\n" + "\n\n".join(
        [f"**{k.title()}:** {v}" for k, v in rat.items() if k != "_summary" and v])

    # Return new_offer dict as 5th value so approval panel can use the exact refined offer
    return new_offer_md, rat_md, explanation, gr_msg, new_offer

# ── Chat (model-aware, dual mode: single-guest or whole-portfolio) ───────────
def chat_respond(msg, history, selected_guest, host_login, model_id, refined_offer, chat_mode):
    """
    Respond to a host chat message.

    chat_mode = "guest"     -> answers about the currently-analyzed guest only
                                (offer details, rationale, talking points, etc.)
    chat_mode = "portfolio" -> answers about the host's WHOLE book of guests
                                (comparisons, rankings, "who should I call first",
                                 cross-guest questions). Selected guest is ignored.

    Single-guest offer data priority (most current first):
      1. refined_offer — if it exists AND belongs to this guest (exact _guest_id
         match), it's the most current state of the offer the host is working with.
      2. Most recently loaded offer for this guest from state_store.
      3. Default freshly-built offer — fallback when neither of the above exists.
    """
    def _err(text):
        return history + [{"role": "user", "content": msg},
                          {"role": "assistant", "content": text}]
    if not host_login: return _err("⚠️ Please log in first.")

    client = get_gemini_for_model(model_id)
    safe_history = []
    for turn in history:
        if isinstance(turn, dict):
            safe_history.append({
                "role":    turn.get("role", "user"),
                "content": _extract_text(turn.get("content", "")),
            })

    if chat_mode == "portfolio":
        portfolio_context = build_portfolio_context(host_login)
        resp = chat_about_portfolio(msg, portfolio_context, safe_history, client)
        return history + [{"role": "user", "content": msg},
                          {"role": "assistant", "content": resp}]

    # ── Single-guest mode (default) ──────────────────────────────────────────
    if not selected_guest: return _err("⚠️ Analyze a guest first, or switch to Portfolio mode above.")
    my    = get_my_guests(host_login)
    guest = next((g for g in my if g["name"] == selected_guest), None)
    if not guest: return _err("⛔ Not your guest.")

    analysis = analyze_guest(guest, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)

    if _refined_offer_matches_guest(refined_offer, guest):
        analysis = dict(analysis)
        analysis["offer"] = refined_offer
    else:
        loaded = get_loaded_offers(host_login=host_login, guest_id=guest["id"])
        if loaded:
            most_recent = loaded[-1]
            analysis = dict(analysis)
            analysis["offer"] = most_recent["offer"]

    resp = chat_with_host(msg, analysis, safe_history, client)
    return history + [{"role": "user", "content": msg},
                      {"role": "assistant", "content": resp}]


def build_portfolio_context(host_login: str) -> str:
    """
    Build the full portfolio summary string for chat_about_portfolio(). Pulls
    every guest's propensity/status/offer-history via get_due_guests (same data
    source as the My Guests tab), plus this session's loaded offers and any
    pending approval requests, so the chat can answer comparative questions
    grounded in the same numbers the host sees elsewhere in the app.
    """
    my = get_my_guests(host_login)
    due_list = get_due_guests(my, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)

    portfolio_summaries = []
    for d in due_list:
        guest_obj = next((g for g in my if g["id"] == d["id"]), None)
        oh = analyze_offer_history(guest_obj, OFFER_HISTORY) if guest_obj else {}
        portfolio_summaries.append({
            "id": d["id"], "name": d["name"], "segment": d["segment"], "tier": d["tier"],
            "propensity_score": d["propensity_score"], "days_overdue": d["days_overdue"],
            "expected_return": d["expected_return"], "avg_trip_value": d["avg_trip_value"],
            "offer_accept_rate": oh.get("accept_rate", 0), "n_offers": oh.get("n_offers", 0),
            "best_channel": oh.get("best_channel", d["primary_contact"]),
        })

    loaded = get_loaded_offers(host_login=host_login)
    loaded_summary = [
        {"guest_name": r["guest_name"], "total": r["offer"].get("total_offer_cost", 0),
         "channel": r["channel"], "loaded_at": r["loaded_at"]}
        for r in loaded
    ]

    pending = [r for r in get_approval_queue(host_login=host_login) if r["status"] == "Pending"]
    pending_summary = [
        {"guest_name": r["guest_name"], "total": r["offer"].get("total_offer_cost", 0),
         "reinvestment_pct": r["reinvestment_pct"], "reason": r["host_reason"]}
        for r in pending
    ]

    host_info = HOSTS.get(host_login, {})
    return build_portfolio_context_prompt(portfolio_summaries, host_info, loaded_summary, pending_summary)


# ── Outreach (model-aware) ────────────────────────────────────────────────────
def generate_outreach(guest_name, channel, host_login, custom_note, model_id, refined_offer):
    """
    Generate outreach content using the REFINED offer if one exists for THIS guest
    (from the Analyze & Refine tab), not a freshly-rebuilt default offer. Without
    this, any refinement the host made (adjusting gaming, food, total, etc.) would
    be silently discarded the moment they switch to the Outreach tab.

    Uses an exact _guest_id tag (set in refine_offer) to confirm the refined offer
    actually belongs to the currently-selected guest, not a leftover from
    refining a different guest earlier in the session.
    """
    if not host_login: return "_Log in first._"
    my    = get_my_guests(host_login)
    guest = next((g for g in my if g["name"] == guest_name), None)
    if not guest: return "⛔ Not your guest."

    analysis  = analyze_guest(guest, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)
    if _refined_offer_matches_guest(refined_offer, guest):
        analysis = dict(analysis)
        analysis["offer"] = refined_offer

    host_info = HOSTS.get(host_login, {})
    client    = get_gemini_for_model(model_id)
    return generate_outreach_content(guest, analysis["offer"], host_info,
                                      channel, custom_note, analysis["contact"], client)


def _refined_offer_matches_guest(refined_offer, guest) -> bool:
    """
    Exact check that a refined offer dict actually belongs to the currently
    selected guest. refine_offer() tags every offer it produces with
    _guest_id = guest["id"] — if that tag is missing or doesn't match, the
    offer is stale (left over from refining a different guest) and must not
    be used here.
    """
    if not refined_offer or not isinstance(refined_offer, dict):
        return False
    if not refined_offer.get("total_offer_cost"):
        return False
    return refined_offer.get("_guest_id") == guest.get("id")

# ── Load offer ────────────────────────────────────────────────────────────────
def do_load_offer(guest_name, host_login, channel, reason, refined_offer):
    """
    Load the REFINED offer to the guest account if one exists for THIS guest,
    not a freshly rebuilt default. This is the function with the highest stakes
    for this bug — loading the wrong offer means the guest gets the wrong comp
    value entirely. See _refined_offer_matches_guest for the exact-ID guard
    against a stale offer from a different guest being applied here.
    """
    if not host_login: return "Log in first."
    my    = get_my_guests(host_login)
    guest = next((g for g in my if g["name"] == guest_name), None)
    if not guest: return "⛔ Not your guest."

    if _refined_offer_matches_guest(refined_offer, guest):
        offer = refined_offer
    else:
        default_analysis = analyze_guest(guest, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)
        offer = default_analysis["offer"]

    status, msg = check_guardrails_full(guest, offer["total_offer_cost"], offer["reinvestment_pct"])
    if status == "hard_block":
        return f"⛔ **Hard Block**\n\n{msg}\n\nAdjust in Refinement panel."
    if status == "needs_approval":
        req = submit_approval_request(
            host_login=host_login, guest_id=guest["id"], guest_name=guest_name,
            segment=guest["segment"], offer_snapshot=copy.deepcopy(offer),
            reinvestment_pct=offer["reinvestment_pct"],
            cap_pct=guest["reinvestment_cap_pct"] * 100,
            hard_cap_pct=APPROVAL_THRESHOLDS.get(guest["segment"], {}).get("hard_cap_pct", 0.45) * 100,
            reason=reason or "Host requesting above-cap offer",
        )
        return (f"📤 **Approval Submitted — {req['id']}**\n\n"
                f"Reinvestment {offer['reinvestment_pct']}% exceeds guest cap. Pending supervisor approval.")
    record = load_offer_to_account(
        host_login=host_login, guest_id=guest["id"], guest_name=guest_name,
        offer_snapshot=copy.deepcopy(offer), channel=channel, notes=reason,
    )
    log_perf_event(host_login, "offer_loaded", guest["id"], offer["total_offer_cost"])
    return (f"✅ **Offer Loaded — {record['id']}**\n\n"
            f"Guest: **{guest_name}** · Comp: **${offer['total_offer_cost']:,}** · "
            f"Reinvestment: {offer['reinvestment_pct']}% ✅ · Channel: {channel}\n"
            f"Loaded at: {record['loaded_at']}")

# ── Approvals ─────────────────────────────────────────────────────────────────
def render_approvals(host_login):
    if not host_login: return []
    is_sup = HOSTS.get(host_login, {}).get("supervisor", False)
    queue  = get_approval_queue(host_login=host_login, supervisor=is_sup)
    rows   = []
    for r in reversed(queue):
        cost = r["offer"].get("total_offer_cost", 0)
        rows.append([r["id"], r["submitted_at"], r["guest_name"], r["segment"],
                     f"${cost:,}", f"{r['reinvestment_pct']:.1f}%",
                     r["host_login"], r["host_reason"][:60], r["status"],
                     r.get("decision_note", "") or ""])
    return rows

APR_HEADERS = ["ID", "Submitted", "Guest", "Segment", "Cost", "Reinvest%",
               "Submitted By", "Reason", "Status", "Note"]

def get_pending_dropdown(host_login):
    """Return dropdown choices of pending requests for the supervisor decision panel."""
    if not host_login:
        return gr.update(choices=[], value=None, info="Log in first.")
    if not HOSTS.get(host_login, {}).get("supervisor"):
        return gr.update(choices=[], value=None,
                         info="Only available to the supervisor account.")
    queue = get_approval_queue(supervisor=True)
    pending = [r for r in queue if r["status"] == "Pending"]
    choices = [
        f"{r['id']} — {r['guest_name']} ({r['segment']}) "
        f"${r['offer'].get('total_offer_cost', 0):,} @ {r['reinvestment_pct']:.1f}%"
        for r in pending
    ]
    return gr.update(
        choices=choices,
        value=choices[0] if choices else None,
        info=f"{len(pending)} pending request(s)" if pending else "No pending requests",
    )

def supervisor_decide(req_id, decision, note, host_login):
    if not host_login: return "Log in first.", []
    if not HOSTS.get(host_login, {}).get("supervisor"):
        return "⛔ Supervisors only.", render_approvals(host_login)
    if not req_id.strip(): return "Enter a request ID.", render_approvals(host_login)
    ok = decide_approval(req_id.strip(), decision, host_login, note)
    if not ok: return f"Request {req_id} not found.", render_approvals(host_login)
    if decision == "Approved":
        from data.state_store import _approval_queue
        req = next((r for r in _approval_queue if r["id"] == req_id.strip()), None)
        if req:
            load_offer_to_account(req["host_login"], req["guest_id"], req["guest_name"],
                                   req["offer"], "Supervisor Approved", note)
    return f"✅ {req_id} → **{decision}**", render_approvals(host_login)

# ── Banner update when model changes ──────────────────────────────────────────
def update_banner(host_login, model_id):
    """Rebuild the session banner to show the active model."""
    if not host_login:
        return "_Not logged in_"
    h     = HOSTS.get(host_login, {})
    label = AVAILABLE_MODELS.get(model_id, model_id)
    short = label.split("—")[0].strip()
    return f"**{h.get('display_name', '')}** · {h.get('title', '')} · 🤖 {short}"

# ══ UI ════════════════════════════════════════════════════════════════════════

TRIP_HEADERS = ["Date", "Room", "Nights", "Gaming P/L", "Food", "Shows", "Spa", "Offers Redeemed"]
OH_HEADERS   = ["Date", "Outcome", "Channel", "Offer Components", "Total", "Notes"]

_THEME = gr.themes.Soft(primary_hue="indigo", secondary_hue="slate")
_CSS   = """
.status-bar{background:#1e293b;color:#e2e8f0;padding:.5rem 1rem;border-radius:8px;font-size:.85rem;margin-bottom:.5rem}
.model-pill{background:#312e81;color:#c7d2fe;padding:.25rem .75rem;border-radius:999px;font-size:.8rem;font-weight:500;white-space:nowrap}
"""

def build_ui():
    with gr.Blocks(title="Kaggle Resort Host Intelligence Agent") as app:

        # ── Shared state ──────────────────────────────────────────────────────
        session_host   = gr.State("")
        selected_guest = gr.State("")
        # Active model ID — default from env, changeable live
        active_model   = gr.State(DEFAULT_MODEL)

        # ── Header row ────────────────────────────────────────────────────────
        with gr.Row(equal_height=True):
            gr.HTML(
                '<div style="padding:.3rem 0">'
                '<h2 style="margin:0">🎰 Kaggle Resort Host Intelligence Agent</h2>'
                '<p style="margin:0;color:#64748b;font-size:.85rem">'
                'Offer Optimization · History-Aware Acceptance · Interactive Refinement</p>'
                '</div>'
            )
            session_banner = gr.Markdown("_Not logged in_", elem_classes=["status-bar"])

        # ── Global model selector bar ─────────────────────────────────────────
        with gr.Row():
            gr.Markdown("**🤖 AI Model:**", scale=0)
            model_selector = gr.Radio(
                choices=MODEL_CHOICES,
                value=DEFAULT_MODEL,
                label="",
                info="Switch model at any time — affects all AI features instantly",
                scale=3,
            )
            model_info = gr.Markdown(
                f"_{AVAILABLE_MODELS.get(DEFAULT_MODEL, '')}_",
                scale=2,
            )

        def on_model_change(model_id, host_login):
            info   = AVAILABLE_MODELS.get(model_id, "")
            banner = update_banner(host_login, model_id)
            return f"_{info}_", banner

        model_selector.change(
            fn=on_model_change,
            inputs=[model_selector, session_host],
            outputs=[model_info, session_banner],
        )
        # Also sync active_model state
        model_selector.change(
            fn=lambda m: m,
            inputs=[model_selector],
            outputs=[active_model],
        )

        with gr.Tabs():

            # ── LOGIN ─────────────────────────────────────────────────────────
            with gr.TabItem("🔑 Login"):
                gr.Markdown("### Host Login")
                with gr.Column(scale=0, min_width=400):
                    login_user = gr.Textbox(label="Username")
                    login_pass = gr.Textbox(label="Password", type="password")
                    login_btn  = gr.Button("Log In", variant="primary")
                    login_msg  = gr.Markdown("")
                gr.Markdown("""**Demo accounts:**
| Username | Password | Role |
|--|--|--|
| `maria.santos` | `maria2026` | Senior Host (Whales) |
| `james.kowalski` | `james2026` | Host (High Rollers) |
| `rita.bloom` | `rita2026` | Host (Premium/Mid-tier) |
| `supervisor` | `super2026` | VP (all guests + approvals) |""")

                def do_login(u, pw, cur, model_id):
                    login, err = authenticate(u, pw)
                    if err:
                        return cur, f"❌ {err}", "_Not logged in_"
                    h      = HOSTS[login]
                    banner = update_banner(login, model_id)
                    return login, f"✅ Welcome, **{h['display_name']}**!", banner

                login_btn.click(
                    fn=do_login,
                    inputs=[login_user, login_pass, session_host, active_model],
                    outputs=[session_host, login_msg, session_banner],
                )

            # ── DASHBOARD ─────────────────────────────────────────────────────
            with gr.TabItem("📊 Dashboard"):
                dash_btn = gr.Button("🔄 Refresh", variant="secondary", scale=0)
                dash_out = gr.Markdown("_Log in to view._")
                dash_btn.click(fn=render_perf_dashboard, inputs=[session_host], outputs=[dash_out])

            # ── GUEST LIST ────────────────────────────────────────────────────
            with gr.TabItem("📋 My Guests"):
                gr.Markdown("Your guests only — ranked by urgency × value. Auto-refreshes on login.")
                with gr.Row():
                    gl_btn = gr.Button("🔄 Manual Refresh", variant="secondary", scale=0)
                    gr.Markdown("🔴 Lapsed · 🟡 Overdue · 🟢 Upcoming · 📋 Offer loaded", scale=3)
                guest_table = gr.Dataframe(headers=GL_HEADERS, datatype=["str"] * 10,
                                           interactive=False, wrap=True)
                gl_btn.click(fn=render_guest_list, inputs=[session_host], outputs=[guest_table])

            # ── ANALYZE + REFINE ──────────────────────────────────────────────
            with gr.TabItem("🔍 Analyze & Refine Offer"):

                def my_names(login):
                    return gr.update(choices=[g["name"] for g in get_my_guests(login)] if login else [])

                with gr.Row():
                    guest_dd    = gr.Dropdown(label="Select Guest", scale=2)
                    analyze_btn = gr.Button("▶ Run Analysis", variant="primary", scale=1)
                session_host.change(fn=my_names, inputs=[session_host], outputs=[guest_dd])

                with gr.Row():
                    with gr.Column(scale=1):
                        profile_out = gr.Markdown()
                        offer_out   = gr.Markdown()
                    with gr.Column(scale=1):
                        rationale_out    = gr.Markdown()
                        ai_rationale_out = gr.Markdown()

                gr.Markdown("### 🤖 AI Host Brief")
                brief_out = gr.Markdown("_Analyze a guest to generate brief._")

                with gr.Accordion("📅 Trip History (last 8 trips)", open=False):
                    trip_table = gr.Dataframe(headers=TRIP_HEADERS, datatype=["str"] * 8,
                                              interactive=False, wrap=True)

                with gr.Accordion("📊 Past Offer History (Accepted/Declined)", open=True):
                    gr.Markdown("_What worked and what didn't — drives the recommendation above._")
                    offer_hist_table = gr.Dataframe(headers=OH_HEADERS, datatype=["str"] * 6,
                                                    interactive=False, wrap=True)

                gr.Markdown("---")
                gr.Markdown("""### ✏️ Refine the Offer
Tell the agent what to change — natural language or specific amounts:
| What to change | How to say it |
|---|---|
| Room type | *"upgrade room to Penthouse Villa"* |
| Gaming comp | *"increase gaming to $5000"* or *"set gaming comp to $3000"* |
| Food comp | *"set food to $1500"* |
| Show | *"add Show VIP"* or *"remove show"* |
| Spa | *"add Spa Package"* or *"remove spa"* |
| Nights | *"change to 4 nights"* |
| **Set total offer** | **"increase total to $6500"** or **"set total to $8000"** |
| Extra budget | *"add $2000 extra budget"* |
| Combined | *"upgrade to Signature Villa, gaming $5000, remove spa, 3 nights"* |

> **Tip — supervisor approval:** If the revised offer exceeds the guest's reinvestment cap, the guardrail will flag it. Go to **Outreach & Load** tab → click **Load Offer to Account** → it will automatically submit an approval request to the supervisor queue.
""")
                with gr.Row():
                    refine_input = gr.Textbox(
                        label="Your changes",
                        placeholder="e.g. upgrade room to Grand Suite, increase gaming comp to $3000",
                        scale=3,
                    )
                    refine_btn = gr.Button("↻ Apply Changes", variant="primary", scale=1)

                with gr.Row():
                    with gr.Column(scale=1):
                        refined_offer_out = gr.Markdown()
                        refined_rat_out   = gr.Markdown()
                    with gr.Column(scale=1):
                        refine_explain_out = gr.Markdown()

                guardrail_state    = gr.State("ok")
                refined_offer_state = gr.State({})  # stores the last refined offer dict

                # Submit for approval — visible only when refined offer exceeds cap
                gr.Markdown("---")
                gr.Markdown("### 📤 Submit Revised Offer for Approval")
                gr.Markdown("_If the revised offer above exceeds the guest's reinvestment cap, "
                             "enter a reason and click Submit. The supervisor will be notified._")
                with gr.Row():
                    approval_reason = gr.Textbox(
                        label="Reason for requesting above-cap offer",
                        placeholder="e.g. Lapsed high-value guest — gaming comp needed to justify the trip from Dallas",
                        scale=3,
                    )
                    submit_approval_btn = gr.Button("📤 Submit for Supervisor Approval", variant="secondary", scale=1)
                approval_result = gr.Markdown()

                def submit_refined_for_approval(guest_name, host_login, reason,
                                                       model_id, refined_offer):
                    if not host_login: return "⚠ Log in first."
                    if not guest_name: return "⚠ Analyze a guest first."
                    my = get_my_guests(host_login)
                    guest = next((g for g in my if g["name"] == guest_name), None)
                    if not guest: return "⛔ Not your guest."

                    # Use the refined offer if available, otherwise fall back to default analysis
                    if refined_offer and isinstance(refined_offer, dict) and refined_offer.get("total_offer_cost"):
                        offer = refined_offer
                    else:
                        offer = analyze_guest(guest, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY)["offer"]

                    status, msg = check_guardrails_full(guest, offer["total_offer_cost"], offer["reinvestment_pct"])
                    if status == "ok":
                        return ("✅ This offer is **within guardrails** — no approval needed. "
                                "Go to Outreach & Load tab to load it directly.")
                    if status == "hard_block":
                        return f"⛔ **Hard Block** — {msg}. Reduce the offer total and try again."

                    # Describe what's in the offer for the supervisor
                    offer_lines = []
                    for key, label in [("room","Room"), ("food_comp","F&B"),
                                       ("gaming_comp","Gaming"), ("show","Show"), ("spa","Spa")]:
                        item = offer.get(key, {})
                        if item and item.get("name"):
                            nights = f" × {offer['room']['nights']}N" if key == "room" else ""
                            offer_lines.append(f"{label}: {item['name']}{nights} (${item.get('cost',0):,})")

                    req = submit_approval_request(
                        host_login=host_login, guest_id=guest["id"], guest_name=guest_name,
                        segment=guest["segment"], offer_snapshot=copy.deepcopy(offer),
                        reinvestment_pct=offer["reinvestment_pct"],
                        cap_pct=guest["reinvestment_cap_pct"] * 100,
                        hard_cap_pct=APPROVAL_THRESHOLDS.get(guest["segment"], {}).get("hard_cap_pct", 0.45) * 100,
                        reason=reason.strip() or "Host requesting above-cap offer",
                    )
                    offer_summary = " · ".join(offer_lines)
                    return (f"📤 **Submitted — {req['id']}**\n\n"
                            f"**Guest:** {guest_name} ({guest['segment']})\n"
                            f"**Offer:** {offer_summary}\n"
                            f"**Total:** ${offer['total_offer_cost']:,} · "
                            f"**Reinvestment:** {offer['reinvestment_pct']}% "
                            f"(cap: {int(guest['reinvestment_cap_pct']*100)}%)\n\n"
                            f"The supervisor can see this in the **Approvals** tab. "
                            f"You'll be notified when a decision is made.")

                submit_approval_btn.click(
                    fn=submit_refined_for_approval,
                    inputs=[selected_guest, session_host, approval_reason,
                            active_model, refined_offer_state],
                    outputs=[approval_result],
                )

                analyze_btn.click(
                    fn=run_analysis,
                    inputs=[guest_dd, session_host, active_model],
                    outputs=[profile_out, offer_out, rationale_out, ai_rationale_out,
                             brief_out, selected_guest, gr.State(), gr.State(), gr.State(),
                             trip_table, offer_hist_table, guardrail_state],
                ).then(
                    # Reset refinement state and clear the revised-offer panels —
                    # a fresh analysis means any prior refinement no longer applies
                    fn=lambda: ({}, "", "", ""),
                    outputs=[refined_offer_state, refined_offer_out, refined_rat_out, refine_explain_out],
                )
                refine_btn.click(
                    fn=refine_offer,
                    inputs=[refine_input, selected_guest, session_host, active_model, refined_offer_state],
                    outputs=[refined_offer_out, refined_rat_out, refine_explain_out,
                             guardrail_state, refined_offer_state],
                )

            # ── OUTREACH + LOAD ───────────────────────────────────────────────
            with gr.TabItem("✉️ Outreach & Load"):
                gr.Markdown("Generate personalized outreach and load the finalized offer to the guest's account.")
                gr.Markdown("_If you refined this guest's offer in the Analyze & Refine tab, that revised offer is used here automatically — no need to redo it._")
                with gr.Row():
                    out_guest = gr.Dropdown(label="Guest", scale=2)
                    out_ch    = gr.Dropdown(
                        choices=["Email", "Phone Call Script", "SMS", "Personal Letter"],
                        value="Email", label="Channel", scale=1,
                    )
                session_host.change(fn=my_names, inputs=[session_host], outputs=[out_guest])

                out_note = gr.Textbox(
                    label="Custom note for AI (optional)",
                    placeholder="e.g. mention his wife's birthday, reference last big win",
                    lines=2,
                )
                gen_btn     = gr.Button("✍️ Generate Content", variant="primary")
                out_content = gr.Markdown("_Content will appear here._")
                gen_btn.click(
                    fn=generate_outreach,
                    inputs=[out_guest, out_ch, session_host, out_note, active_model, refined_offer_state],
                    outputs=[out_content],
                )

                gr.Markdown("---")
                gr.Markdown("### 📥 Load Offer to Guest Account")
                gr.Markdown("_Uses the revised offer from the Analyze & Refine tab if you made changes there — otherwise uses the default offer._")
                with gr.Row():
                    load_ch     = gr.Dropdown(
                        choices=["Email", "Phone", "SMS", "In-person", "Mail"],
                        value="Email", label="Delivery channel", scale=1,
                    )
                    load_reason = gr.Textbox(
                        label="Notes / reason", scale=2,
                        placeholder="e.g. anniversary trip — justified premium offer",
                    )
                load_btn    = gr.Button("📥 Load Offer to Account", variant="primary")
                load_result = gr.Markdown()
                load_btn.click(
                    fn=do_load_offer,
                    inputs=[out_guest, session_host, load_ch, load_reason, refined_offer_state],
                    outputs=[load_result],
                )

            # ── CHAT ──────────────────────────────────────────────────────────
            with gr.TabItem("💬 Host AI Chat"):
                gr.Markdown("""Ask about one guest, or switch to **Portfolio** mode to ask about your whole book —
*"Who should I call first this week?"* · *"Which guest has the best acceptance rate?"* · *"Compare Derek and Marcus"* ·
*"Who's overdue and high-value?"* · *"What's the last offer loaded?"*

The active model shown at the top of the page is used for all responses. Switch it anytime.""")

                chat_mode_toggle = gr.Radio(
                    choices=[("🧑 This Guest", "guest"), ("📂 My Whole Portfolio", "portfolio")],
                    value="guest",
                    label="Chat scope",
                    info="Guest mode uses the guest selected in Analyze & Refine. Portfolio mode ignores that and reasons over all your guests at once.",
                )

                chatbot   = gr.Chatbot()
                with gr.Row():
                    chat_in  = gr.Textbox(placeholder="Ask anything…", label="", scale=4)
                    chat_btn = gr.Button("Send ↗", variant="primary", scale=1)
                clear_btn = gr.Button("🗑 Clear", variant="secondary")

                chat_btn.click(
                    fn=chat_respond,
                    inputs=[chat_in, chatbot, selected_guest, session_host, active_model,
                            refined_offer_state, chat_mode_toggle],
                    outputs=[chatbot],
                ).then(lambda: "", outputs=[chat_in])
                chat_in.submit(
                    fn=chat_respond,
                    inputs=[chat_in, chatbot, selected_guest, session_host, active_model,
                            refined_offer_state, chat_mode_toggle],
                    outputs=[chatbot],
                ).then(lambda: "", outputs=[chat_in])
                clear_btn.click(lambda: [], outputs=[chatbot])


            # ── APPROVALS ─────────────────────────────────────────────────────
            with gr.TabItem("✅ Approvals"):
                gr.Markdown("""**Hosts** — see your submitted requests and their status here.
**Supervisor** — select a pending request from the dropdown, choose Approved or Rejected, add a note, and submit.""")

                apr_refresh = gr.Button("🔄 Refresh Queue", variant="secondary")
                apr_table   = gr.Dataframe(headers=APR_HEADERS, datatype=["str"] * 10,
                                           interactive=False, wrap=True)

                gr.Markdown("---")
                gr.Markdown("### Supervisor Decision Panel")
                gr.Markdown("_Only visible to the supervisor account. Select a request from the dropdown below._")

                # Dropdown populated from the pending queue — much easier than typing an ID
                apr_dd = gr.Dropdown(
                    choices=[], label="Select Request to Decide",
                    info="Shows all Pending requests. Refresh the queue first if you don't see new ones.",
                    scale=2,
                )

                # get_pending_dropdown is defined at module level below render_approvals

                with gr.Row():
                    apr_dec  = gr.Dropdown(choices=["Approved", "Rejected"], value="Approved",
                                           label="Decision", scale=1)
                    apr_note = gr.Textbox(label="Decision note", scale=3,
                                          placeholder="e.g. Approved — lapsed high-value guest warrants premium gaming comp")
                apr_btn    = gr.Button("✅ Submit Decision", variant="primary")
                apr_result = gr.Markdown()

                def supervisor_decide_from_dd(apr_dd_value, decision, note, host_login):
                    """Extract request ID from the dropdown label and decide."""
                    if not host_login: return "Log in first.", [], gr.update(choices=[])
                    if not HOSTS.get(host_login, {}).get("supervisor"):
                        return "⛔ Supervisors only.", render_approvals(host_login), gr.update()
                    if not apr_dd_value:
                        return "⚠ Select a request from the dropdown first.", render_approvals(host_login), gr.update()
                    # Extract ID from "APR-0001 — Guest Name..." format
                    req_id = apr_dd_value.split(" — ")[0].strip()
                    ok = decide_approval(req_id, decision, host_login, note)
                    if not ok:
                        return f"Request {req_id} not found.", render_approvals(host_login), gr.update()
                    if decision == "Approved":
                        from data.state_store import _approval_queue
                        req = next((r for r in _approval_queue if r["id"] == req_id), None)
                        if req:
                            load_offer_to_account(
                                req["host_login"], req["guest_id"], req["guest_name"],
                                req["offer"], "Supervisor Approved", note,
                            )
                    rows = render_approvals(host_login)
                    new_choices = get_pending_dropdown(host_login)
                    return (f"✅ **{req_id} → {decision}**\n\n"
                            f"{'Offer has been loaded to the guest account.' if decision == 'Approved' else 'Request rejected. Host will be notified.'}"),                           rows, new_choices

                apr_refresh.click(fn=render_approvals,        inputs=[session_host], outputs=[apr_table])
                apr_refresh.click(fn=get_pending_dropdown,    inputs=[session_host], outputs=[apr_dd])
                apr_btn.click(
                    fn=supervisor_decide_from_dd,
                    inputs=[apr_dd, apr_dec, apr_note, session_host],
                    outputs=[apr_result, apr_table, apr_dd],
                )

            # ── ABOUT ─────────────────────────────────────────────────────────
            with gr.TabItem("ℹ️ About"):
                gr.Markdown(f"""
## Kaggle Resort — Host Intelligence Agent

**Google × Kaggle 5-Day AI Agents Vibe Coding Capstone · June 2026 · Track: Agents for Business**

### Available Models (switch live using the selector at the top)
| Model ID | Free RPD | Strength |
|----------|----------|----------|
| `gemini-2.5-flash` | 20/day | Best prose quality — recommended for demo |
| `gemini-3.1-flash-lite` | 500/day | Fastest + strongest benchmarks — best for testing |
| `gemini-3.5-flash` | 20/day | Newest 3.5 series |

**Default model** (set via `GEMINI_MODEL` env var in HF Space settings): `{DEFAULT_MODEL}`

### Features
| Feature | Description |
|---------|-------------|
| 📊 Past offer history | 57 historical accepted/declined offers across all 14 guests |
| 🧠 History-aware acceptance | Acceptance probability blends propensity score + historical rate |
| ⚠️ Must-have detection | Detects required components from decline patterns |
| ✏️ Interactive refinement | Natural language offer changes with live guardrail feedback |
| 🤖 Live model selector | Switch Gemini models mid-session without restarting |
| 📋 Per-component rationale | Every offer component explained with data reasoning |
| 🔐 Host access control | Each host sees only their own portfolio |
| ✅ Approval workflow | Over-cap offers routed to supervisor queue |

### Course Concepts
| Day | Concept | Implementation |
|-----|---------|----------------|
| Day 1 | Agents & vibe coding | Gemini brief, rationale, refinement, outreach |
| Day 2 | Tools & interoperability | MCP server · ADK agents · FunctionTool |
| Day 3 | Memory & context | Session state · Offer history · Chat memory |
| Day 4 | Quality & security | Access control · Approval workflow · Hard blocks |
| Day 5 | Prototype to production | HF Spaces · Graceful API key fallback |

**Stack:** Gemini 2.5 / 3.1 / 3.5 · Google ADK · FastMCP · Gradio 6.x · HuggingFace Spaces
**Data:** All guest data synthetic — no real PII. Source files never mutated at runtime.
""")

        # ── Auto-refresh all data on login (session_host.change fires when login succeeds) ──
        session_host.change(fn=render_guest_list,     inputs=[session_host], outputs=[guest_table])
        session_host.change(fn=render_perf_dashboard, inputs=[session_host], outputs=[dash_out])
        session_host.change(
            fn=lambda login: gr.update(choices=[g["name"] for g in get_my_guests(login)] if login else []),
            inputs=[session_host], outputs=[guest_dd]
        )
        session_host.change(
            fn=lambda login: gr.update(choices=[g["name"] for g in get_my_guests(login)] if login else []),
            inputs=[session_host], outputs=[out_guest]
        )
        # Auto-refresh approvals table and dropdown on login
        session_host.change(fn=render_approvals,     inputs=[session_host], outputs=[apr_table])
        session_host.change(fn=get_pending_dropdown, inputs=[session_host], outputs=[apr_dd])

    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, theme=_THEME, css=_CSS)
