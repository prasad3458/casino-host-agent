"""
Casino Host Agent Engine v2
Changes: acceptance model uses offer history · build_offer returns rationale ·
         apply_offer_adjustments for interactive refinement · history-aware simulate_roi

ENGINE_BUILD fingerprint lets us verify which exact version of this file is
running on a live deployment, independent of app.py's own fingerprint. If the
two fingerprints ever disagree (app.py shows one build, but this string is
missing or different from what's expected), the deployed files are out of sync.
"""

ENGINE_BUILD = "2026-06-30-totalfix-v3"

import math
from datetime import date, datetime

# ── Date helpers ──────────────────────────────────────────────────────────────

def today():
    return date.today()

def days_since(date_str: str) -> int:
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (today() - d).days

def expected_return_date(avg_days: float, last_visit: str) -> str:
    import datetime as dt
    last = datetime.strptime(last_visit, "%Y-%m-%d").date()
    exp  = last + dt.timedelta(days=int(avg_days))
    return exp.strftime("%b %d, %Y")

# ── Trip analytics ─────────────────────────────────────────────────────────────

def compute_trip_analytics(guest: dict) -> dict:
    trips = guest["trips"]
    n = len(trips)
    if n < 2:
        avg_gap = 365
    else:
        dates = sorted([datetime.strptime(t["date"], "%Y-%m-%d").date() for t in trips])
        gaps  = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_gap = sum(gaps) / len(gaps)

    gaming_losses = [abs(t["gaming_win_loss"]) for t in trips if t["gaming_win_loss"] < 0]
    avg_gaming    = sum(gaming_losses) / len(gaming_losses) if gaming_losses else 0

    total_spends  = [abs(t["gaming_win_loss"]) + t["food_spend"] + t["show_spend"] + t["spa_spend"] for t in trips]
    avg_total     = sum(total_spends) / len(total_spends)

    if n >= 4:
        recent  = sum(abs(t["gaming_win_loss"]) for t in trips[-2:]) / 2
        earlier = sum(abs(t["gaming_win_loss"]) for t in trips[:-2]) / (n - 2)
        trend   = (recent - earlier) / earlier * 100 if earlier > 0 else 0
    else:
        trend = 0

    days_overdue = days_since(guest["last_visit"]) - avg_gap

    return {
        "n_trips": n,
        "avg_gap_days": round(avg_gap),
        "days_since_last": days_since(guest["last_visit"]),
        "days_overdue": round(days_overdue),
        "avg_gaming_loss": round(avg_gaming),
        "avg_total_trip_value": round(avg_total),
        "gaming_trend_pct": round(trend, 1),
        "expected_return_date": expected_return_date(avg_gap, guest["last_visit"]),
    }

# ── Offer history analysis ─────────────────────────────────────────────────────

def analyze_offer_history(guest: dict, offer_history: dict) -> dict:
    """
    Mine past offers for this guest to extract:
    - which components were present in accepted vs declined offers
    - channel acceptance rates
    - minimum thresholds that seem required for a yes
    """
    gid      = guest["id"]
    history  = offer_history.get(gid, [])
    accepted = [h for h in history if h["outcome"] == "Accepted"]
    declined = [h for h in history if h["outcome"] == "Declined"]

    n_total   = len(history)
    n_accept  = len(accepted)
    accept_rate = round(n_accept / n_total * 100) if n_total else 50

    # Component presence rates in accepted vs declined
    def comp_rate(records, key):
        if not records: return 0
        present = sum(1 for r in records if r["offer"].get(key) and r["offer"][key] is not None)
        return round(present / len(records) * 100)

    # Channel rates
    channel_counts = {}
    for h in history:
        ch = h.get("channel","Unknown")
        channel_counts.setdefault(ch, {"total":0,"accepted":0})
        channel_counts[ch]["total"] += 1
        if h["outcome"] == "Accepted":
            channel_counts[ch]["accepted"] += 1
    channel_rates = {ch: round(v["accepted"]/v["total"]*100) for ch, v in channel_counts.items()}

    # What was present in all accepted offers (must-haves)
    must_have_gaming = comp_rate(accepted, "gaming") >= 75 and comp_rate(declined, "gaming") < 50
    must_have_show   = comp_rate(accepted, "show")   >= 75 and comp_rate(declined, "show")   < 50
    must_have_spa    = comp_rate(accepted, "spa")    >= 75 and comp_rate(declined, "spa")    < 50

    # Minimum gaming amount in accepted offers
    gaming_amounts_accepted = [h["offer"].get("gaming") for h in accepted if h["offer"].get("gaming")]
    def parse_gaming_amt(s):
        if not s: return 0
        try: return int(str(s).replace("Gaming $","").replace(",","").split()[0])
        except: return 0
    min_gaming_accepted = min([parse_gaming_amt(g) for g in gaming_amounts_accepted], default=0) if gaming_amounts_accepted else 0

    # Best channel
    best_channel = max(channel_rates, key=channel_rates.get) if channel_rates else guest["contact_pref"][0]

    # Decline reasons summary
    decline_reasons = [h["notes"] for h in declined]

    return {
        "n_offers": n_total,
        "n_accepted": n_accept,
        "accept_rate": accept_rate,
        "must_have_gaming": must_have_gaming,
        "must_have_show": must_have_show,
        "must_have_spa": must_have_spa,
        "min_gaming_accepted": min_gaming_accepted,
        "channel_rates": channel_rates,
        "best_channel": best_channel,
        "gaming_in_accepted_pct": comp_rate(accepted, "gaming"),
        "show_in_accepted_pct": comp_rate(accepted, "show"),
        "spa_in_accepted_pct": comp_rate(accepted, "spa"),
        "decline_reasons": decline_reasons,
        "recent_declined": declined[-1]["notes"] if declined else None,
    }

# ── Propensity scoring ─────────────────────────────────────────────────────────

def score_propensity(guest: dict, analytics: dict,
                     offer_history: dict = None) -> dict:
    score = 50
    overdue = analytics["days_overdue"]
    if overdue > 180: score -= 15
    elif overdue > 90: score += 5
    elif overdue > 30: score += 15
    elif overdue > 0:  score += 10
    else:              score += 5

    n = analytics["n_trips"]
    if n >= 8:   score += 15
    elif n >= 5: score += 10
    elif n >= 3: score += 5

    trend = analytics["gaming_trend_pct"]
    if trend > 10:   score += 10
    elif trend > 0:  score += 5
    elif trend < -10:score -= 8

    seg_bonus = {"Whale": 10, "High Roller": 8, "Premium": 6, "Mid-tier": 4, "Developing": 3}
    score += seg_bonus.get(guest["segment"], 0)

    # Boost/penalise from offer history
    if offer_history:
        oh = analyze_offer_history(guest, offer_history)
        if oh["accept_rate"] >= 75: score += 8
        elif oh["accept_rate"] >= 50: score += 4
        elif oh["accept_rate"] < 25: score -= 6

    score = max(5, min(95, score))

    avg_val    = analytics["avg_total_trip_value"]
    val_bucket  = "High" if avg_val >= 10000 else "Low"
    prop_bucket = "High" if score >= 55 else "Low"
    quadrant_map = {
        ("High","High"): "Priority Reactivation — maximize offer, act now",
        ("High","Low"):  "Strategic Investment — strong value, needs the right hook",
        ("Low","High"):  "Warm Nurture — keep engaged, grow over time",
        ("Low","Low"):   "Maintenance — minimal spend, standard offer",
    }
    return {
        "score": score,
        "value_bucket": val_bucket,
        "propensity_bucket": prop_bucket,
        "quadrant": quadrant_map[(val_bucket, prop_bucket)],
    }

# ── Offer builder ──────────────────────────────────────────────────────────────

def build_offer(guest: dict, analytics: dict, propensity: dict,
                offer_catalog: dict, guardrails: dict,
                offer_history: dict = None,
                overrides: dict = None) -> dict:
    """
    Build optimal offer. overrides can pin specific components:
      overrides = {
        "room": "Penthouse Villa",          # pin room type (or None to let engine choose)
        "nights": 3,                  # pin nights
        "gaming_amount": 5000,        # pin exact gaming dollar amount
        "food_amount": 2000,          # pin exact F&B dollar amount
        "show": "Show VIP",           # pin show (or "remove")
        "spa": "remove",              # "remove" = explicitly exclude
        "extra_budget": 2000,         # add to base budget
      }
    Returns offer dict + rationale dict.
    """
    segment    = guest["segment"]
    cap_pct    = guest.get("reinvestment_cap_pct", 0.30)
    avg_gaming = analytics["avg_gaming_loss"]
    base_budget = round(avg_gaming * cap_pct)
    hard_cap    = guardrails["max_total_offer_cost"][segment]
    ov          = overrides or {}
    extra_budget = ov.get("extra_budget", 0)
    budget      = min(base_budget + extra_budget, hard_cap)
    score       = propensity["score"]
    rationale   = {}   # populated below for each component

    # History insights
    oh = analyze_offer_history(guest, offer_history) if offer_history else {}

    # ── ROOM ─────────────────────────────────────────────────────────────────
    eligible_rooms = {n: i for n, i in offer_catalog["rooms"].items()
                      if segment in i["eligible_segments"]}
    sorted_rooms   = sorted(eligible_rooms.items(), key=lambda x: x[1]["comp_cost"], reverse=True)

    pinned_room = ov.get("room")
    if pinned_room and pinned_room in offer_catalog["rooms"]:
        room_name, room_info = pinned_room, offer_catalog["rooms"][pinned_room]
        rationale["room"] = f"Host specified {pinned_room}."
    else:
        # Check if history shows a room floor (declined for too-low room)
        if oh.get("decline_reasons"):
            # Look for "not nice enough" / "downgrade" signals in decline notes
            room_floor_signal = any("room" in r.lower() and ("not nice" in r.lower() or "downgrade" in r.lower() or "minimum" in r.lower())
                                    for r in oh.get("decline_reasons",[]))
        else:
            room_floor_signal = False

        if score >= 70 or room_floor_signal:
            room_name, room_info = sorted_rooms[0]
            rationale["room"] = f"High propensity ({score}/100) or history shows guest expects premium room — selected top eligible tier ({room_name})."
        elif score >= 50:
            room_name, room_info = sorted_rooms[min(1, len(sorted_rooms)-1)]
            rationale["room"] = f"Moderate propensity ({score}/100) — mid-tier room ({room_name}) balances quality and cost."
        else:
            room_name, room_info = sorted_rooms[-1]
            rationale["room"] = f"Conservative propensity ({score}/100) — entry-level eligible room ({room_name}) to manage cost."

    pinned_nights = ov.get("nights")
    if pinned_nights:
        room_nights = int(pinned_nights)
        rationale["nights"] = f"Host specified {room_nights} nights."
    else:
        room_nights = 3 if score >= 60 else 2
        rationale["nights"] = f"{room_nights} nights based on propensity score ({score}/100)."

    room_cost = room_info["comp_cost"] * room_nights
    remaining = budget - room_cost

    # ── FOOD ─────────────────────────────────────────────────────────────────
    pinned_food_amt = ov.get("food_amount")
    food_name = food_cost_val = None
    if ov.get("food") == "remove":
        rationale["food"] = "Host removed food comp."
    elif pinned_food_amt:
        # Find closest catalog item at or below pinned amount
        candidates = {k: v for k, v in offer_catalog["food_comps"].items()
                      if segment in v["eligible_segments"] and v["cost"] <= pinned_food_amt}
        if candidates:
            food_name, fi = max(candidates.items(), key=lambda x: x[1]["cost"])
            food_cost_val = fi["cost"]
            rationale["food"] = f"Host specified ${pinned_food_amt} F&B → best catalog match: {food_name}."
        else:
            rationale["food"] = f"No eligible food comp at ${pinned_food_amt} for {segment} segment."
    else:
        eligible_food = {k: v for k, v in offer_catalog["food_comps"].items()
                         if segment in v["eligible_segments"] and v["cost"] <= remaining}
        if eligible_food:
            food_name, fi = max(eligible_food.items(), key=lambda x: x[1]["cost"])
            food_cost_val = fi["cost"]
            avg_food = analytics["avg_total_trip_value"] - analytics["avg_gaming_loss"]
            rationale["food"] = f"Guest's avg non-gaming spend is ${avg_food:,.0f}/trip — {food_name} aligns with their on-property F&B behaviour."
    if food_cost_val: remaining -= food_cost_val

    # ── GAMING ───────────────────────────────────────────────────────────────
    gaming_name = gaming_cost_val = None
    pinned_gaming_amt = ov.get("gaming_amount")
    if ov.get("gaming") == "remove":
        rationale["gaming"] = "Host removed gaming comp."
    elif analytics["n_trips"] < guardrails["min_trips_for_gaming_comp"] and not pinned_gaming_amt:
        rationale["gaming"] = f"Fewer than {guardrails['min_trips_for_gaming_comp']} trips — gaming comp not yet earned."
    else:
        # Determine effective floor from history
        hist_floor = oh.get("min_gaming_accepted", 0)
        must_have  = oh.get("must_have_gaming", False)
        if pinned_gaming_amt:
            # Round UP to the nearest catalog tier at or above the requested amount —
            # if the host says "increase gaming to 5000" they want at least $5000,
            # not the highest tier that happens to be cheaper than $5000.
            at_or_above = {k: v for k, v in offer_catalog["gaming_comps"].items()
                           if segment in v["eligible_segments"] and v["cost"] >= pinned_gaming_amt}
            if at_or_above:
                gaming_name, gi = min(at_or_above.items(), key=lambda x: x[1]["cost"])
                gaming_cost_val = gi["cost"]
                rationale["gaming"] = f"Host requested ${pinned_gaming_amt:,} gaming → nearest tier at or above: {gaming_name}."
            else:
                # No tier reaches that high — use the maximum eligible tier instead
                at_or_below = {k: v for k, v in offer_catalog["gaming_comps"].items()
                              if segment in v["eligible_segments"]}
                if at_or_below:
                    gaming_name, gi = max(at_or_below.items(), key=lambda x: x[1]["cost"])
                    gaming_cost_val = gi["cost"]
                    rationale["gaming"] = f"Host requested ${pinned_gaming_amt:,} but no catalog tier reaches that — using maximum eligible: {gaming_name}."
                else:
                    rationale["gaming"] = f"No eligible gaming comp tier for {segment} segment."
        else:
            candidates = {k: v for k, v in offer_catalog["gaming_comps"].items()
                          if segment in v["eligible_segments"] and v["cost"] <= remaining}
            if candidates:
                gaming_name, gi = max(candidates.items(), key=lambda x: x[1]["cost"])
                gaming_cost_val = gi["cost"]
                hist_note = f" History shows minimum ${hist_floor:,} needed for acceptance." if hist_floor > 0 else ""
                must_note  = " Gaming comp is present in 75%+ of accepted offers for this guest." if must_have else ""
                rationale["gaming"] = f"Selected {gaming_name} within remaining budget.{hist_note}{must_note}"
            elif must_have and remaining < hist_floor:
                rationale["gaming"] = f"⚠️ Gaming comp required by history but budget too tight after room. Consider reducing room or increasing budget."
            else:
                rationale["gaming"] = "No gaming comp fits remaining budget."
    if gaming_cost_val: remaining -= gaming_cost_val

    # ── SHOW ─────────────────────────────────────────────────────────────────
    show_name = show_cost_val = None
    past_show = sum(t.get("show_spend",0) for t in guest["trips"])
    must_show  = oh.get("must_have_show", False)
    if ov.get("show") == "remove":
        rationale["show"] = "Host removed show comp."
    elif ov.get("show") and ov.get("show") != "remove":
        pinned = ov["show"]
        if pinned in offer_catalog["shows"]:
            show_name     = pinned
            show_cost_val = offer_catalog["shows"][pinned]["cost"]
            rationale["show"] = f"Host specified {pinned}."
    elif (past_show > 0 or must_show) and remaining > 0:
        candidates = {k: v for k, v in offer_catalog["shows"].items()
                      if segment in v["eligible_segments"] and v["cost"] <= remaining}
        if candidates:
            show_name, si = max(candidates.items(), key=lambda x: x[1]["cost"])
            show_cost_val = si["cost"]
            must_note = " Guest history shows shows are a must-have for acceptance." if must_show else ""
            rationale["show"] = f"Guest has ${past_show:,} in past show spend.{must_note} Included {show_name}."
        else:
            rationale["show"] = "No show comp fits remaining budget."
    else:
        rationale["show"] = "Guest has no show history — excluded to preserve budget."
    if show_cost_val: remaining -= show_cost_val

    # ── SPA ──────────────────────────────────────────────────────────────────
    spa_name = spa_cost_val = None
    past_spa  = sum(t.get("spa_spend",0) for t in guest["trips"])
    must_spa  = oh.get("must_have_spa", False)
    if ov.get("spa") == "remove":
        rationale["spa"] = "Host removed spa comp."
    elif ov.get("spa") and ov.get("spa") != "remove":
        pinned = ov["spa"]
        if pinned in offer_catalog["spa"]:
            spa_name     = pinned
            spa_cost_val = offer_catalog["spa"][pinned]["cost"]
            rationale["spa"] = f"Host specified {pinned}."
    elif (past_spa > 100 or must_spa) and remaining > 0:
        candidates = {k: v for k, v in offer_catalog["spa"].items()
                      if segment in v["eligible_segments"] and v["cost"] <= remaining}
        if candidates:
            spa_name, sp = max(candidates.items(), key=lambda x: x[1]["cost"])
            spa_cost_val = sp["cost"]
            must_note = " Guest history shows spa is a must-have for acceptance." if must_spa else ""
            rationale["spa"] = f"Guest averages ${past_spa/max(1,analytics['n_trips']):,.0f} spa/trip.{must_note} Included {spa_name}."
        else:
            rationale["spa"] = "No spa comp fits remaining budget."
    else:
        rationale["spa"] = "Guest has minimal spa history — excluded."
    if spa_cost_val: remaining -= spa_cost_val

    total_cost      = room_cost + (food_cost_val or 0) + (gaming_cost_val or 0) + (show_cost_val or 0) + (spa_cost_val or 0)
    reinvest_pct    = round(total_cost / avg_gaming * 100, 1) if avg_gaming > 0 else 0
    within          = reinvest_pct <= cap_pct * 100 and total_cost <= hard_cap

    # Overall offer rationale
    history_summary = ""
    if oh:
        history_summary = (f"Based on {oh['n_offers']} past offers ({oh['accept_rate']}% acceptance rate). "
                           f"Best channel: {oh.get('best_channel','N/A')}. ")
        if oh.get("decline_reasons"):
            history_summary += f"Last decline reason: \"{oh['decline_reasons'][-1][:120]}\"."

    rationale["_summary"] = (
        f"{history_summary}"
        f"Propensity score {propensity['score']}/100 ({propensity['quadrant']}). "
        f"Total offer ${total_cost:,} = {reinvest_pct}% reinvestment "
        f"(guest cap {int(cap_pct*100)}%, budget ${budget:,}). "
        f"[engine-build: {ENGINE_BUILD}]"
    )

    return {
        "room":         {"name": room_name, "nights": room_nights, "cost": room_cost, "rack_rate": room_info.get("rack_rate",0)},
        "food_comp":    {"name": food_name,    "cost": food_cost_val},
        "gaming_comp":  {"name": gaming_name,  "cost": gaming_cost_val},
        "show":         {"name": show_name,    "cost": show_cost_val},
        "spa":          {"name": spa_name,     "cost": spa_cost_val},
        "total_offer_cost": total_cost,
        "reinvestment_pct": reinvest_pct,
        "budget_available": budget,
        "within_guardrails": within,
        "rationale": rationale,
        "offer_history_summary": oh,
    }

# ── History-aware ROI simulation ───────────────────────────────────────────────

def simulate_roi(guest: dict, offer: dict, propensity: dict,
                 analytics: dict, offer_history: dict = None) -> dict:
    base_prob = propensity["score"] / 100
    oh = offer.get("offer_history_summary") or (analyze_offer_history(guest, offer_history) if offer_history else {})

    # Component attractiveness
    items = sum([
        1 if offer["food_comp"].get("name") else 0,
        1 if offer["gaming_comp"].get("name") else 0,
        1 if offer["show"].get("name") else 0,
        1 if offer["spa"].get("name") else 0,
    ])
    attract_boost = min(0.15, items * 0.04)

    # History adjustment: if must-have components present/absent
    hist_boost = 0.0
    hist_penalty = 0.0
    missing_musthaves = []
    if oh:
        if oh.get("must_have_gaming") and not offer["gaming_comp"].get("name"):
            hist_penalty += 0.15
            missing_musthaves.append("gaming comp")
        if oh.get("must_have_show") and not offer["show"].get("name"):
            hist_penalty += 0.12
            missing_musthaves.append("show")
        if oh.get("must_have_spa") and not offer["spa"].get("name"):
            hist_penalty += 0.10
            missing_musthaves.append("spa")
        # Bonus if we're above the historical minimum gaming threshold
        if oh.get("min_gaming_accepted", 0) > 0 and offer["gaming_comp"].get("cost",0) >= oh["min_gaming_accepted"]:
            hist_boost += 0.08
        # Anchor to historical acceptance rate
        hist_base = oh.get("accept_rate", 50) / 100
        base_prob = (base_prob + hist_base) / 2   # blend propensity + history

    accept_prob = min(0.93, max(0.05, base_prob + attract_boost + hist_boost - hist_penalty))

    expected_gaming = analytics["avg_gaming_loss"]
    expected_food   = analytics["avg_total_trip_value"] - analytics["avg_gaming_loss"]
    expected_rev    = expected_gaming + expected_food
    expected_net    = expected_rev - offer["total_offer_cost"]

    low_rev  = round(expected_rev * 0.75)
    high_rev = round(expected_rev * 1.25)
    breakeven = offer["total_offer_cost"] / expected_rev if expected_rev > 0 else 1

    return {
        "accept_probability_pct": round(accept_prob * 100, 1),
        "expected_revenue_if_visit": expected_rev,
        "expected_net_if_visit": round(expected_net),
        "ev_net": round(accept_prob * expected_net),
        "revenue_range": f"${low_rev:,} – ${high_rev:,}",
        "breakeven_accept_prob_pct": round(breakeven * 100, 1),
        "roi_ratio": round(expected_net / offer["total_offer_cost"], 1) if offer["total_offer_cost"] > 0 else 0,
        "missing_must_haves": missing_musthaves,
        "history_adjusted": bool(oh),
    }

# ── Apply host adjustments (interactive refinement) ───────────────────────────
# NOTE: This function now accepts PRE-PARSED overrides from the LLM
# (see agents/gemini_agent.py: parse_refinement_with_llm), not raw regex
# matching against the instruction text. The host's natural language is
# interpreted by Gemini, which understands intent, vague phrasing, and
# guest-context tradeoffs — this function only EXECUTES the resulting
# structured plan against the catalog and guardrails. That split (LLM for
# understanding, deterministic code for execution/guardrails) keeps the
# system auditable: every dollar amount placed in the final offer can be
# traced to a catalog lookup, not to a hallucinated number.

def apply_offer_adjustments(llm_overrides: dict, current_offer: dict,
                             guest: dict, analytics: dict, propensity: dict,
                             offer_catalog: dict, guardrails: dict,
                             offer_history: dict = None) -> dict:
    """
    Apply LLM-parsed overrides on top of the current (possibly already-refined)
    offer, so successive refinements compound rather than resetting to default.

    llm_overrides is produced by gemini_agent.parse_refinement_with_llm() and
    may contain: room, nights, gaming_amount, gaming="remove", food_amount,
    food="remove", show, show="remove", spa, spa="remove", _target_total,
    _llm_reasoning.

    Returns the new offer dict (with rationale) plus an "_llm_reasoning" key
    if the LLM provided one, so the UI can show how the request was interpreted.
    """
    overrides = {}
    carried_keys = set()  # tracks which override keys came from carry-forward, not this instruction

    # ── Carry forward the prior offer's component choices as a baseline ──────
    # Makes successive refinements COMPOUND instead of resetting: if gaming was
    # already pushed to $5000 in a prior step, a new instruction that only
    # touches the show comp should not silently reset gaming to the default.
    prior_room   = current_offer.get("room", {})
    prior_gaming = current_offer.get("gaming_comp", {})
    prior_food   = current_offer.get("food_comp", {})
    prior_show   = current_offer.get("show", {})
    prior_spa    = current_offer.get("spa", {})

    if prior_room.get("name"):
        overrides["room"] = prior_room["name"]; carried_keys.add("room")
    if prior_room.get("nights"):
        overrides["nights"] = prior_room["nights"]; carried_keys.add("nights")
    if prior_gaming.get("cost"):
        overrides["gaming_amount"] = prior_gaming["cost"]; carried_keys.add("gaming_amount")
    if prior_food.get("cost"):
        overrides["food_amount"] = prior_food["cost"]; carried_keys.add("food_amount")
    if prior_show.get("name"):
        overrides["show"] = prior_show["name"]; carried_keys.add("show")
    if prior_spa.get("name"):
        overrides["spa"] = prior_spa["name"]; carried_keys.add("spa")

    prior_total = current_offer.get("total_offer_cost", 0)
    base_budget_estimate = round(analytics.get("avg_gaming_loss", 0) * guest.get("reinvestment_cap_pct", 0.3))
    if prior_total > base_budget_estimate:
        overrides["extra_budget"] = prior_total - base_budget_estimate
        carried_keys.add("extra_budget")

    # ── Apply the LLM's explicit instructions — these always win over carry-forward ──
    llm_reasoning = llm_overrides.get("_llm_reasoning", "")

    if llm_overrides.get("room"):
        overrides["room"] = llm_overrides["room"]
        carried_keys.discard("room")
    if llm_overrides.get("nights"):
        overrides["nights"] = llm_overrides["nights"]
        carried_keys.discard("nights")

    if llm_overrides.get("gaming") == "remove":
        overrides["gaming"] = "remove"
        carried_keys.discard("gaming_amount")
    elif llm_overrides.get("gaming_amount"):
        overrides["gaming_amount"] = llm_overrides["gaming_amount"]
        carried_keys.discard("gaming_amount")

    if llm_overrides.get("food") == "remove":
        overrides["food"] = "remove"
        carried_keys.discard("food_amount")
    elif llm_overrides.get("food_amount"):
        overrides["food_amount"] = llm_overrides["food_amount"]
        carried_keys.discard("food_amount")

    if llm_overrides.get("show") == "remove":
        overrides["show"] = "remove"
        carried_keys.discard("show")
    elif llm_overrides.get("show"):
        overrides["show"] = llm_overrides["show"]
        carried_keys.discard("show")

    if llm_overrides.get("spa") == "remove":
        overrides["spa"] = "remove"
        carried_keys.discard("spa")
    elif llm_overrides.get("spa"):
        overrides["spa"] = llm_overrides["spa"]
        carried_keys.discard("spa")

    # ── Target total: the LLM extracted a desired TOTAL offer value ──────────
    # (e.g. host said "bring it up to around 6500" or "increase gaming so the
    # total goes to 6500"). We compute the delta vs the current chained total
    # and push it into gaming, since gaming comp correlates most with acceptance.
    #
    # Defensive check: an LLM occasionally echoes the CURRENT gaming amount back
    # in its JSON even when the host's real intent was a total-based change (e.g.
    # it states "gaming_amount": 3000 where 3000 IS the current value, not a new
    # one). If the "explicit" gaming_amount equals what gaming already costs in
    # the current offer, that's not a real change — don't let it block target_total.
    current_gaming_cost = current_offer.get("gaming_comp", {}).get("cost") or 0
    gaming_overrides_value = overrides.get("gaming_amount")
    gaming_is_explicit = (
        "gaming_amount" in overrides
        and "gaming_amount" not in carried_keys
        and gaming_overrides_value != current_gaming_cost
    )
    target_total = llm_overrides.get("_target_total")

    if target_total and not gaming_is_explicit:
        current_total = current_offer.get("total_offer_cost", 0)
        delta = target_total - current_total
        if delta > 0:
            current_gaming = current_offer.get("gaming_comp", {}).get("cost") or 0
            target_gaming = current_gaming + delta
            segment = guest["segment"]
            tiers_above = sorted(
                [(k, v) for k, v in offer_catalog["gaming_comps"].items()
                 if segment in v["eligible_segments"] and v["cost"] >= target_gaming],
                key=lambda x: x[1]["cost"]
            )
            if tiers_above:
                overrides["gaming_amount"] = tiers_above[0][1]["cost"]
            else:
                all_eligible = sorted(
                    [(k, v) for k, v in offer_catalog["gaming_comps"].items()
                     if segment in v["eligible_segments"]],
                    key=lambda x: x[1]["cost"]
                )
                if all_eligible:
                    overrides["gaming_amount"] = all_eligible[-1][1]["cost"]
            carried_keys.discard("gaming_amount")
            overrides["extra_budget"] = delta + 1000  # buffer so room/food aren't squeezed out
            carried_keys.discard("extra_budget")
        elif delta < 0:
            current_gaming = current_offer.get("gaming_comp", {}).get("cost") or 0
            reduced = max(0, current_gaming + delta)
            if reduced > 0:
                overrides["gaming_amount"] = reduced
                carried_keys.discard("gaming_amount")

    result = build_offer(guest, analytics, propensity, offer_catalog, guardrails,
                         offer_history=offer_history, overrides=overrides)
    if llm_reasoning:
        result["rationale"]["_llm_reasoning"] = llm_reasoning
    return result


# ── Contact strategy ───────────────────────────────────────────────────────────

def recommend_contact(guest: dict, analytics: dict, propensity: dict,
                      guardrails: dict, offer_history: dict = None) -> dict:
    oh = analyze_offer_history(guest, offer_history) if offer_history else {}
    prefs   = guest["contact_pref"]
    primary = oh.get("best_channel") or prefs[0]   # history overrides preference if available
    rules   = guardrails["contact_time_rules"]

    if analytics["days_overdue"] > 150:
        urgency  = "High — guest may be defecting"
        sequence = f"1) {primary} this week  2) Follow-up in 7 days  3) Re-contact in 14 days if no response"
    elif analytics["days_overdue"] > 60:
        urgency  = "Moderate — past cadence baseline"
        sequence = f"1) {primary} outreach  2) Follow-up in 10 days if no response"
    elif analytics["days_overdue"] > 0:
        urgency  = "Standard — just past their usual window"
        sequence = f"1) {primary} outreach with offer"
    else:
        urgency  = "Proactive — upcoming window"
        sequence = f"1) Send offer 2 weeks before expected return ({analytics['expected_return_date']})"

    talking_points = []
    if guest.get("notes"):
        talking_points.append(f"Personal note: {guest['notes']}")
    if analytics["gaming_trend_pct"] > 5:
        talking_points.append("Gaming trending up — mention growing momentum")
    if analytics["n_trips"] >= 5:
        talking_points.append(f"Acknowledge loyalty — {analytics['n_trips']} visits")
    if oh.get("recent_declined"):
        talking_points.append(f"Last decline reason: {oh['recent_declined'][:100]} — address this proactively")
    if oh.get("channel_rates"):
        best = max(oh["channel_rates"], key=oh["channel_rates"].get)
        talking_points.append(f"Best channel by history: {best} ({oh['channel_rates'][best]}% acceptance rate)")

    return {
        "primary_channel": primary,
        "all_channels": prefs,
        "timing_rule": rules.get(primary, "Standard business hours"),
        "urgency": urgency,
        "outreach_sequence": sequence,
        "talking_points": talking_points,
        "channel_rates": oh.get("channel_rates", {}),
    }

# ── Full analysis ──────────────────────────────────────────────────────────────

def analyze_guest(guest: dict, offer_catalog: dict, guardrails: dict,
                  offer_history: dict = None, overrides: dict = None) -> dict:
    analytics  = compute_trip_analytics(guest)
    propensity = score_propensity(guest, analytics, offer_history)
    offer      = build_offer(guest, analytics, propensity, offer_catalog, guardrails,
                             offer_history=offer_history, overrides=overrides)
    simulation = simulate_roi(guest, offer, propensity, analytics, offer_history)
    contact    = recommend_contact(guest, analytics, propensity, guardrails, offer_history)
    return {
        "guest": guest, "analytics": analytics, "propensity": propensity,
        "offer": offer, "simulation": simulation, "contact": contact,
    }

# ── Guest list ─────────────────────────────────────────────────────────────────

def get_due_guests(guests: list, offer_catalog: dict, guardrails: dict,
                   offer_history: dict = None) -> list:
    results = []
    for g in guests:
        a = compute_trip_analytics(g)
        p = score_propensity(g, a, offer_history)
        results.append({
            "id": g["id"], "name": g["name"], "segment": g["segment"], "tier": g["tier"],
            "days_since_last": a["days_since_last"], "days_overdue": a["days_overdue"],
            "avg_trip_value": a["avg_total_trip_value"], "propensity_score": p["score"],
            "quadrant": p["quadrant"], "primary_contact": g["contact_pref"][0],
            "expected_return": a["expected_return_date"],
        })
    results.sort(key=lambda x: (-max(0, x["days_overdue"]), -(x["propensity_score"] * x["avg_trip_value"])))
    return results
