"""
Gemini conversational layer v2
New: offer rationale narration · history-aware context · refinement explanations
     Live model switching — model_id passed per-call from the UI selector
"""

import os

# Default model — override via GEMINI_MODEL env var in HF Space settings
# gemini-2.5-flash:      20 RPD free  | best prose quality
# gemini-3.1-flash-lite: 500 RPD free | fastest + smartest benchmarks
# gemini-3.5-flash:      20 RPD free  | newest 3.5 series
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """You are an expert resort host advisor at Kaggle Resort, a premier integrated resort.
You help resort hosts understand their guests, craft optimal reinvestment offers, and plan outreach.
Your tone is professional, concise, and actionable — like a seasoned VP of Player Development.

You always ground answers in the data provided. Never invent figures.
Keep responses under 350 words unless asked for more. No bullet-point walls — write in clear prose."""

def get_model(model_id: str = None):
    """
    Return a Gemini client for the requested model.
    model_id defaults to GEMINI_MODEL env var (gemini-2.5-flash).
    Returns None if GEMINI_API_KEY is not set — app runs in analytics-only mode.
    The active model ID is stored on the client as client._active_model.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        client._active_model = model_id or GEMINI_MODEL
        return client
    except:
        return None

def _model_id(client) -> str:
    """Extract the active model ID from a client object."""
    if client is None:
        return GEMINI_MODEL
    return getattr(client, "_active_model", GEMINI_MODEL)


# ── LLM-driven natural-language offer refinement ──────────────────────────────
# This replaces brittle regex/keyword matching with an actual LLM call that
# understands intent, ambiguity, and tradeoffs the way a host would phrase them —
# e.g. "make it more generous", "match what worked last time", "he needs more
# than last time but stay reasonable" are not pattern-matchable but ARE
# understandable by an LLM given the current offer and catalog as context.

REFINEMENT_PARSER_PROMPT = """You are a precise instruction parser for a casino host offer system.
You read a host's natural-language request and the CURRENT offer state, then output
ONLY a JSON object describing what should change. You do not explain, narrate, or add
any text outside the JSON.

AVAILABLE OFFER CATALOG FOR THIS GUEST'S SEGMENT ({segment}):
Rooms (cost is per night): {rooms_json}
Food & Beverage comps: {food_json}
Gaming comps: {gaming_json}
Shows: {shows_json}
Spa: {spa_json}

CURRENT OFFER STATE:
Room: {cur_room} × {cur_nights} nights (${cur_room_cost}/night)
Food: {cur_food} (${cur_food_cost})
Gaming: {cur_gaming} (${cur_gaming_cost})
Show: {cur_show} (${cur_show_cost})
Spa: {cur_spa} (${cur_spa_cost})
Current total: ${cur_total}

GUEST CONTEXT (use this to interpret vague requests like "make it more generous"
or "what worked last time"):
{guest_context}

HOST'S REQUEST: "{instruction}"

Output a JSON object with ONLY the keys that should change. Valid keys:
- "room": exact room name string from the catalog above, or omit if unchanged
- "nights": integer, or omit if unchanged
- "gaming_amount": integer dollar target for gaming comp (the system will pick the
  closest catalog tier at or above this number), or omit if unchanged
- "gaming_remove": true if gaming should be removed entirely
- "food_amount": integer dollar target for food comp, or omit if unchanged
- "food_remove": true if food should be removed entirely
- "show": exact show name string from the catalog, or omit if unchanged
- "show_remove": true if show should be removed
- "spa": exact spa name string from the catalog, or omit if unchanged
- "spa_remove": true if spa should be removed
- "target_total": integer — if the host specifies a desired TOTAL offer value
  (e.g. "increase total to 6500", "bring it up to around 7000", "keep it under 5000"),
  put the target number here. The system will figure out how to allocate it.
- "reasoning": a short (1 sentence) explanation of how you interpreted the request

EXAMPLES (study these patterns carefully):

Host says: "increase gaming to make the total 6500"
Correct output: {{"target_total": 6500, "reasoning": "Host wants the overall offer to reach $6500, achieved by raising gaming."}}
WRONG output (do not do this): {{"gaming_amount": 3000, "reasoning": "..."}}  ← this guesses
gaming_amount instead of letting the system solve for it. The host did not give a gaming
dollar figure — they gave a TOTAL figure with gaming as the lever. Always use target_total here.

Host says: "set gaming to 3000"
Correct output: {{"gaming_amount": 3000, "reasoning": "Host specified an exact gaming comp amount."}}
This is correct because the dollar figure (3000) is attached directly to "gaming", with no
mention of "total" at all.

Host says: "bump the total up to around 8000"
Correct output: {{"target_total": 8000, "reasoning": "Host wants overall offer near $8000."}}

Host says: "give him more gaming, maybe another 2000 on top"
Correct output: {{"gaming_amount": <current_gaming_cost + 2000>, "reasoning": "Host wants gaming increased by $2000 over current."}}
Here you DO compute a number, but it is a gaming-specific instruction ("more gaming... on
top"), not a total-outcome instruction — the distinguishing signal is the absence of the
word "total" and the explicit attachment of the dollar change to gaming itself.

RULES:
- CRITICAL: never do the dollar math yourself for a total-based request. If the host's
  phrasing connects a component change to a TOTAL outcome — patterns like "increase
  gaming to make the total X", "increase gaming so the total is X", "raise gaming until
  we hit X total", "get the total up to X" — this is ALWAYS a target_total instruction.
  Output ONLY "target_total": X. Do NOT also output "gaming_amount" — the system will
  calculate the correct gaming figure itself by working backward from the target total
  and the current offer. You computing gaming_amount yourself for these phrasings is the
  single most common mistake — avoid it. The words "to make the total" or "so the total"
  mean: solve for the total, not for gaming directly.
- Only set "gaming_amount" when the host states an exact dollar figure that IS the gaming
  comp itself, with no reference to a total outcome — e.g. "set gaming to $3000", "gaming
  comp of $5000", "bump gaming up to 4000". These have no "total" word connecting them.
- Never set "gaming_amount" to the CURRENT/unchanged value just to "confirm" it — omit the
  key entirely if gaming itself is not what the host gave a new number for.
- If the host's request is vague (e.g. "make it more generous", "be more aggressive"),
  use the guest context and history to decide a reasonable increase — typically increase
  gaming_amount by 20-40% over current, since gaming comps drive acceptance most.
- If the host's request is vague in the conservative direction ("dial it back",
  "be more careful", "reduce risk"), reduce gaming_amount by 20-30%.
- If the host references "what worked last time" or "the formula that converts",
  use the guest context's accepted offer history to pick matching values.
- Only include keys that should actually change. Do not repeat unchanged values.
- Output ONLY the JSON object. No markdown fences, no commentary, no explanation outside the JSON.
"""

def parse_refinement_with_llm(instruction: str, current_offer: dict, guest: dict,
                                offer_catalog: dict, offer_history_summary: dict,
                                client) -> dict:
    """
    Use the LLM to interpret a natural-language refinement instruction against
    the current offer state and guest context. Returns a dict of overrides
    compatible with engine.build_offer()'s overrides parameter.

    Falls back to a minimal regex-based parse ONLY if no API key is configured —
    this keeps the app functional without a key, but the LLM path is now primary.
    """
    if client is None:
        return _fallback_regex_parse(instruction, current_offer)

    segment = guest.get("segment", "")

    def _filter_segment(catalog_section, cost_key="cost"):
        return {k: v[cost_key] for k, v in catalog_section.items()
                if segment in v.get("eligible_segments", [])}

    import json as _json
    rooms_json  = _json.dumps(_filter_segment(offer_catalog["rooms"], "comp_cost"))
    food_json   = _json.dumps(_filter_segment(offer_catalog["food_comps"]))
    gaming_json = _json.dumps(_filter_segment(offer_catalog["gaming_comps"]))
    shows_json  = _json.dumps(_filter_segment(offer_catalog["shows"]))
    spa_json    = _json.dumps(_filter_segment(offer_catalog["spa"]))

    room = current_offer.get("room", {})
    food = current_offer.get("food_comp", {})
    gaming = current_offer.get("gaming_comp", {})
    show = current_offer.get("show", {})
    spa = current_offer.get("spa", {})

    guest_context = (
        f"Notes: {guest.get('notes','')}. "
        f"Past offer acceptance rate: {offer_history_summary.get('accept_rate','N/A')}%. "
        f"Must-have gaming: {offer_history_summary.get('must_have_gaming', False)}. "
        f"Minimum gaming that historically converted: ${offer_history_summary.get('min_gaming_accepted', 0):,}. "
        f"Best channel: {offer_history_summary.get('best_channel','N/A')}."
    )

    prompt = REFINEMENT_PARSER_PROMPT.format(
        segment=segment,
        rooms_json=rooms_json, food_json=food_json, gaming_json=gaming_json,
        shows_json=shows_json, spa_json=spa_json,
        cur_room=room.get("name", "None"), cur_nights=room.get("nights", 0),
        cur_room_cost=room.get("cost", 0),
        cur_food=food.get("name", "None"), cur_food_cost=food.get("cost") or 0,
        cur_gaming=gaming.get("name", "None"), cur_gaming_cost=gaming.get("cost") or 0,
        cur_show=show.get("name", "None"), cur_show_cost=show.get("cost") or 0,
        cur_spa=spa.get("name", "None"), cur_spa_cost=spa.get("cost") or 0,
        cur_total=current_offer.get("total_offer_cost", 0),
        guest_context=guest_context,
        instruction=instruction,
    )

    try:
        from google import genai
        response = client.models.generate_content(
            model=_model_id(client),
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        raw = response.text.strip()
        # Strip markdown fences if the model adds them despite instructions
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        parsed = _json.loads(raw)
        engine_overrides = _llm_overrides_to_engine_overrides(parsed)
        # Deterministic safety net (does not depend on the LLM following the prompt
        # perfectly): if the host's raw text explicitly mentions "total" with a number,
        # and the LLM returned a guessed gaming_amount instead of target_total, override
        # it here. This guarantees correct behavior even if the model ignores the rules.
        engine_overrides = _enforce_total_language_override(instruction, engine_overrides)
        return engine_overrides
    except Exception as e:
        # If the LLM call fails for any reason, fall back to regex rather than crashing
        fallback = _fallback_regex_parse(instruction, current_offer)
        fallback["_llm_error"] = str(e)[:150]
        return fallback


def _enforce_total_language_override(instruction: str, engine_overrides: dict) -> dict:
    """
    Deterministic guardrail against LLM non-compliance: if the host's raw instruction
    text contains the word "total" near a number, that ALWAYS means target_total —
    regardless of what gaming_amount (if any) the LLM also returned. This protects
    against the model computing its own (often wrong) gaming dollar figure instead of
    deferring to the engine's target_total solver.
    """
    import re
    instr_lower = instruction.lower()
    nd = instr_lower.replace("$", "").replace(",", "")
    total_match = re.search(r"total\D{0,15}?(\d{3,6})", nd)
    if not total_match:
        total_match = re.search(r"(\d{3,6})\D{0,15}?total", nd)

    if total_match:
        stated_total = int(total_match.group(1))
        # Force target_total to the value explicitly stated in the host's own words,
        # and drop any gaming_amount the LLM may have guessed — let the engine's
        # target_total solver (in apply_offer_adjustments) compute the real gaming figure.
        engine_overrides["_target_total"] = stated_total
        engine_overrides.pop("gaming_amount", None)
        engine_overrides.pop("food_amount", None)
        existing_reasoning = engine_overrides.get("_llm_reasoning", "")
        engine_overrides["_llm_reasoning"] = (
            f"{existing_reasoning} [Total target of ${stated_total:,} detected directly in "
            f"your request and enforced — gaming will be calculated to reach this total.]"
        ).strip()
    return engine_overrides


def _llm_overrides_to_engine_overrides(parsed: dict) -> dict:
    """Translate the LLM's JSON schema into engine.build_offer()'s overrides format."""
    overrides = {}
    if "room" in parsed and parsed["room"]:
        overrides["room"] = parsed["room"]
    if "nights" in parsed and parsed["nights"]:
        overrides["nights"] = int(parsed["nights"])
    if parsed.get("gaming_remove"):
        overrides["gaming"] = "remove"
    elif "gaming_amount" in parsed and parsed["gaming_amount"]:
        overrides["gaming_amount"] = int(parsed["gaming_amount"])
    if parsed.get("food_remove"):
        overrides["food"] = "remove"
    elif "food_amount" in parsed and parsed["food_amount"]:
        overrides["food_amount"] = int(parsed["food_amount"])
    if parsed.get("show_remove"):
        overrides["show"] = "remove"
    elif "show" in parsed and parsed["show"]:
        overrides["show"] = parsed["show"]
    if parsed.get("spa_remove"):
        overrides["spa"] = "remove"
    elif "spa" in parsed and parsed["spa"]:
        overrides["spa"] = parsed["spa"]
    if "target_total" in parsed and parsed["target_total"]:
        overrides["_target_total"] = int(parsed["target_total"])
    if "reasoning" in parsed:
        overrides["_llm_reasoning"] = parsed["reasoning"]
    return overrides


def _fallback_regex_parse(instruction: str, current_offer: dict) -> dict:
    """
    Minimal fallback ONLY used when no GEMINI_API_KEY is configured, or if the
    LLM call itself fails (network error, quota, JSON parse error, etc). This is
    explicitly the degraded path — it cannot understand vague or compound natural
    language the way the LLM path can. Handles only the most explicit, literal cases.

    CRITICAL ORDERING: total-language detection runs FIRST. The naive approach of
    checking gaming-amount patterns first is wrong — "increase gaming amount to make
    the total close to 6000" contains the word "gaming" followed eventually by a
    number, so a greedy \\D*(\\d+) pattern incorrectly captures 6000 as a gaming
    dollar figure before "total" is ever checked. Checking total-language first and
    exiting early when found avoids this entirely.
    """
    import re
    instr = instruction.lower().strip()
    nd = instr.replace("$", "").replace(",", "")
    overrides = {}

    # ── Total-language check FIRST — if "total" appears near a number, that
    # number describes the TOTAL outcome, not any single component, regardless
    # of what other component words (gaming, food) also appear in the sentence.
    total_match = re.search(r'total\D{0,20}?(\d+)', nd)
    if not total_match:
        total_match = re.search(r'(\d+)\D{0,20}?total', nd)

    if total_match:
        overrides["_target_total"] = int(total_match.group(1))
        # Still check for explicit removal instructions, which are unambiguous
        # regardless of total-language elsewhere in the sentence.
        if "remove spa" in instr or "no spa" in instr:
            overrides["spa"] = "remove"
        if "remove show" in instr or "no show" in instr:
            overrides["show"] = "remove"
        overrides["_llm_reasoning"] = ("Parsed via simplified fallback rules (no API key configured, "
                                       "or the AI request failed) — total-based instruction detected. "
                                       "For full natural-language understanding, configure GEMINI_API_KEY.")
        return overrides

    # ── No total-language found — safe to check component-specific amounts ──
    gm = re.search(r'gaming\D*(\d+)', nd) or re.search(r'(\d+)\D*gaming', nd)
    if gm and gm.group(1):
        overrides["gaming_amount"] = int(gm.group(1))
    elif "remove gaming" in instr or "no gaming" in instr:
        overrides["gaming"] = "remove"

    fm = re.search(r'food\D*(\d+)', nd) or re.search(r'f&b\D*(\d+)', nd)
    if fm and fm.group(1):
        overrides["food_amount"] = int(fm.group(1))
    elif "remove food" in instr or "no food" in instr:
        overrides["food"] = "remove"

    if "remove spa" in instr or "no spa" in instr:
        overrides["spa"] = "remove"
    elif "spa" in instr:
        # Try to find a literal spa name match — handled properly in engine carry-forward
        pass

    if "remove show" in instr or "no show" in instr:
        overrides["show"] = "remove"
    elif "show vip" in instr:
        overrides["show"] = "Show VIP"
    elif "show x2" in instr:
        overrides["show"] = "Show x2"
    elif "show x1" in instr or ("show" in instr and "add" in instr):
        overrides["show"] = "Show x1"

    nights_m = re.search(r'(\d+)\s*night', nd)
    if nights_m:
        overrides["nights"] = int(nights_m.group(1))

    overrides["_llm_reasoning"] = ("Parsed via simplified fallback rules (no API key configured, "
                                   "or the AI request failed) — for full natural-language understanding "
                                   "of vague or compound requests, configure GEMINI_API_KEY.")
    return overrides

def build_context_prompt(analysis: dict) -> str:
    g = analysis["guest"]
    a = analysis["analytics"]
    p = analysis["propensity"]
    o = analysis["offer"]
    s = analysis["simulation"]
    c = analysis["contact"]
    oh = o.get("offer_history_summary", {})

    offer_lines = []
    for key, label in [("room","Room"),("food_comp","F&B"),("gaming_comp","Gaming"),("show","Show"),("spa","Spa")]:
        item = o[key]
        if item.get("name"):
            nights = f" × {o['room']['nights']}N" if key=="room" else ""
            offer_lines.append(f"  {label}: {item['name']}{nights} (${item.get('cost',0):,})")

    history_block = ""
    if oh:
        history_block = f"""
OFFER HISTORY ({oh.get('n_offers',0)} past offers, {oh.get('accept_rate',0)}% acceptance):
  Best channel: {oh.get('best_channel','N/A')} | Channel rates: {oh.get('channel_rates',{})}
  Must-have gaming: {oh.get('must_have_gaming',False)} | Must-have show: {oh.get('must_have_show',False)} | Must-have spa: {oh.get('must_have_spa',False)}
  Min gaming that converted: ${oh.get('min_gaming_accepted',0):,}
  Last decline reason: {oh.get('recent_declined','None')}"""

    rationale_block = ""
    rat = o.get("rationale", {})
    if rat:
        parts = [f"  {k}: {v}" for k, v in rat.items() if k != "_summary"]
        rationale_block = "\nOFFER RATIONALE (per component):\n" + "\n".join(parts)
        if rat.get("_summary"):
            rationale_block += f"\n  SUMMARY: {rat['_summary']}"

    return f"""GUEST: {g['name']} | Segment: {g['segment']} | Tier: {g['tier']}
City: {g['city']} | Age: {g['age']} | Contact pref: {', '.join(g['contact_pref'])}
Notes: {g.get('notes','')}

ANALYTICS:
  Trips: {a['n_trips']} | Avg gap: {a['avg_gap_days']}d | Days since last: {a['days_since_last']} | Overdue: {a['days_overdue']}d
  Avg gaming loss/trip: ${a['avg_gaming_loss']:,} | Avg total/trip: ${a['avg_total_trip_value']:,} | Trend: {a['gaming_trend_pct']:+.1f}%
  Expected return: {a['expected_return_date']}

PROPENSITY: {p['score']}/100 — {p['quadrant']}
{history_block}

RECOMMENDED OFFER:
{chr(10).join(offer_lines)}
  TOTAL: ${o['total_offer_cost']:,} | Reinvestment: {o['reinvestment_pct']}% (cap: {int(g['reinvestment_cap_pct']*100)}%)
  Guardrails: {"✓ OK" if o['within_guardrails'] else "⚠ EXCEEDS"}
{rationale_block}

ROI SIMULATION:
  Acceptance probability: {s['accept_probability_pct']}% (history-adjusted: {s['history_adjusted']})
  Revenue if visit: ${s['expected_revenue_if_visit']:,} | Net after offer: ${s['expected_net_if_visit']:,}
  ROI: {s['roi_ratio']}x | Missing must-haves: {s['missing_must_haves']}

CONTACT: {c['primary_channel']} | {c['urgency']}
Sequence: {c['outreach_sequence']}
Talking points: {'; '.join(c['talking_points'][:3])}
Channel performance: {c.get('channel_rates',{})}
"""

def get_initial_brief(analysis: dict, client) -> str:
    if client is None:
        return _fallback_brief(analysis)
    ctx = build_context_prompt(analysis)
    prompt = f"""{SYSTEM_PROMPT}

{ctx}

Write a sharp host brief covering:
1. Status & urgency (1-2 sentences)
2. The recommended offer — and the single most compelling reason THIS guest will say yes to it (draw from their history)
3. Expected return vs cost (one sentence)
4. Exactly how and when to reach out
5. One risk to flag
"""
    try:
        from google import genai
        return client.models.generate_content(model=_model_id(client), contents=prompt).text
    except Exception as e:
        return _fallback_brief(analysis) + f"\n\n[Gemini unavailable: {str(e)[:80]}]"

def generate_offer_rationale(analysis: dict, client) -> str:
    """
    Generate a single-paragraph, plain-English explanation of why this offer
    was constructed this way — for display in the UI next to the offer.
    """
    if client is None:
        return _fallback_rationale(analysis)
    ctx = build_context_prompt(analysis)
    prompt = f"""{SYSTEM_PROMPT}

{ctx}

Write ONE paragraph (4-6 sentences, no bullet points, no headers) explaining why this specific offer was recommended.
Cover: why each component was chosen or excluded, what the guest's history tells us about what drives acceptance,
and what the key risk is if any component is removed.
Be specific — reference actual dollar amounts, acceptance rates, and decline reasons from the data.
Write as if briefing the host verbally before a phone call.
"""
    try:
        from google import genai
        return client.models.generate_content(model=_model_id(client), contents=prompt).text
    except Exception as e:
        return _fallback_rationale(analysis) + f" [Gemini unavailable: {str(e)[:80]}]"

def explain_refinement(instruction: str, old_offer: dict, new_offer: dict,
                        analysis: dict, client) -> str:
    """
    After the host has adjusted an offer, explain what changed and the impact.
    """
    if client is None:
        return _fallback_refinement_explanation(instruction, old_offer, new_offer)
    ctx = build_context_prompt(analysis)

    def offer_summary(o):
        parts = []
        for key in ["room","food_comp","gaming_comp","show","spa"]:
            item = o[key]
            if item.get("name"):
                nights = f"×{o['room']['nights']}N" if key=="room" else ""
                parts.append(f"{item['name']}{nights} (${item.get('cost',0):,})")
        return ", ".join(parts) if parts else "empty"

    prompt = f"""{SYSTEM_PROMPT}

{ctx}

The host requested this change: "{instruction}"

Previous offer: {offer_summary(old_offer)} — Total: ${old_offer['total_offer_cost']:,} ({old_offer['reinvestment_pct']}%)
New offer: {offer_summary(new_offer)} — Total: ${new_offer['total_offer_cost']:,} ({new_offer['reinvestment_pct']}%)
New guardrail status: {"✓ Within limits" if new_offer['within_guardrails'] else "⚠ Exceeds cap"}

Write 2-3 sentences explaining: what changed, the impact on total cost and reinvestment rate,
and whether this change improves or risks the likelihood of acceptance based on this guest's history.
Be direct and specific.
"""
    try:
        from google import genai
        return client.models.generate_content(model=_model_id(client), contents=prompt).text
    except Exception as e:
        return _fallback_refinement_explanation(instruction, old_offer, new_offer)

def _extract_text(content) -> str:
    """
    Safely extract plain text from a Gradio 6 message content field.
    Gradio 6 can pass content as: str, list of dicts (multimodal), or None.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Gradio 6 multimodal: [{"type": "text", "text": "..."}, ...]
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts)
    return str(content)


def chat_with_host(user_message: str, analysis: dict, history: list, client) -> str:
    if client is None:
        return ("\u26a0 Gemini API key not configured. Add GEMINI_API_KEY as a Space secret. "
                "All analytics, offers, simulations, and offer history still work without it.")
    ctx  = build_context_prompt(analysis)
    full = SYSTEM_PROMPT + "\n\nGuest data:\n" + ctx + "\n\nConversation:\n"

    # Robustly handle Gradio 6 dict format, enriched objects, or legacy [[user,bot]] pairs
    for turn in history:
        try:
            if isinstance(turn, dict):
                role    = "Host" if turn.get("role") == "user" else "Advisor"
                content = _extract_text(turn.get("content", ""))
                full   += role + ": " + content + "\n"
            elif isinstance(turn, (list, tuple)) and len(turn) == 2:
                full += "Host: " + _extract_text(turn[0]) + "\n"
                full += "Advisor: " + _extract_text(turn[1]) + "\n"
        except Exception:
            continue  # skip malformed turns rather than crashing

    full += "Host: " + user_message + "\nAdvisor:"
    try:
        from google import genai
        return client.models.generate_content(model=_model_id(client), contents=full).text
    except Exception as e:
        return "I encountered an error processing that request. Please try again. (Detail: " + str(e)[:100] + ")"


# ── Portfolio-wide chat (all of a host's guests, not just one) ───────────────
# This is a separate context builder from build_context_prompt — instead of one
# guest's full analysis, it summarizes EVERY guest in the host's portfolio so
# the host can ask comparative or portfolio-level questions: "who should I call
# first this week", "which of my guests has the best acceptance rate", "who's
# overdue and high-value", "compare Derek and Marcus", etc.

def build_portfolio_context_prompt(portfolio_summaries: list, host_info: dict,
                                    loaded_offers_summary: list,
                                    pending_approvals_summary: list) -> str:
    """
    Build a compact, scannable summary of every guest in the host's portfolio.
    Designed to fit many guests in a reasonable token budget — one line each,
    not the full per-guest detail that build_context_prompt produces for a
    single guest. Gemini reasons over this table to answer portfolio-level
    questions without needing every guest's full trip history.
    """
    lines = [f"HOST: {host_info.get('display_name','Unknown')} ({host_info.get('title','')})",
             f"PORTFOLIO SIZE: {len(portfolio_summaries)} guests\n",
             "GUEST SUMMARY TABLE:"]
    for g in portfolio_summaries:
        lines.append(
            f"- {g['name']} (ID {g['id']}) | {g['segment']}/{g['tier']} | "
            f"propensity {g['propensity_score']}/100 | "
            f"{'OVERDUE +' + str(g['days_overdue']) + 'd' if g['days_overdue'] > 0 else 'upcoming, due ' + g['expected_return']} | "
            f"avg trip value ${g['avg_trip_value']:,} | "
            f"offer history: {g['offer_accept_rate']}% accept ({g['n_offers']} offers) | "
            f"best channel: {g['best_channel']}"
        )

    if loaded_offers_summary:
        lines.append("\nOFFERS LOADED THIS SESSION:")
        for o in loaded_offers_summary:
            lines.append(f"- {o['guest_name']}: ${o['total']:,} via {o['channel']} at {o['loaded_at']}")

    if pending_approvals_summary:
        lines.append("\nPENDING SUPERVISOR APPROVALS:")
        for a in pending_approvals_summary:
            lines.append(f"- {a['guest_name']}: ${a['total']:,} ({a['reinvestment_pct']:.1f}%) — {a['reason'][:80]}")

    return "\n".join(lines)


def chat_about_portfolio(user_message: str, portfolio_context: str, history: list, client) -> str:
    """
    Like chat_with_host, but operates over the WHOLE portfolio summary instead
    of a single guest's detailed analysis. Use this when the host hasn't
    selected a specific guest, or asks a comparative/portfolio-level question.
    """
    if client is None:
        return ("\u26a0 Gemini API key not configured. Add GEMINI_API_KEY as a Space secret. "
                "Portfolio chat requires the AI connection — guest analysis and offers still work without it.")

    full = (SYSTEM_PROMPT + "\n\nYou are looking at the host's FULL PORTFOLIO, not a single guest. "
            "Answer comparative and portfolio-level questions (who to call first, ranking by "
            "value or urgency, comparing guests) using only the data below. If the host asks about "
            "details not in this summary (e.g. full trip history for one guest), tell them to select "
            "that guest in the Analyze tab for deeper detail, rather than guessing.\n\n"
            + portfolio_context + "\n\nConversation:\n")

    for turn in history:
        try:
            if isinstance(turn, dict):
                role    = "Host" if turn.get("role") == "user" else "Advisor"
                content = _extract_text(turn.get("content", ""))
                full   += role + ": " + content + "\n"
            elif isinstance(turn, (list, tuple)) and len(turn) == 2:
                full += "Host: " + _extract_text(turn[0]) + "\n"
                full += "Advisor: " + _extract_text(turn[1]) + "\n"
        except Exception:
            continue

    full += "Host: " + user_message + "\nAdvisor:"
    try:
        from google import genai
        return client.models.generate_content(model=_model_id(client), contents=full).text
    except Exception as e:
        return "I encountered an error processing that request. Please try again. (Detail: " + str(e)[:100] + ")"

def generate_outreach_content(guest, offer, host_info, channel, custom_note, contact, client) -> str:
    g = guest
    offer_summary = []
    for key in ["room","food_comp","gaming_comp","show","spa"]:
        item = offer[key]
        if item.get("name"):
            nights = f" × {offer['room']['nights']} nights" if key=="room" else ""
            offer_summary.append(f"{item['name']}{nights}")
    from data.guests import GUARDRAILS
    ch_lower = channel.lower()
    extra = f"\nAdditional note: {custom_note}" if custom_note.strip() else ""

    if "email" in ch_lower:
        prompt = f"""Write a personalized resort host email from {host_info.get('display_name','Your Host')} to {g['name']}.
Offer: {', '.join(offer_summary)}. Guest notes: {g.get('notes','')}.
Contact preference history: {contact.get('channel_rates',{})}.
- Subject line first
- Warm opening referencing something specific about their history
- Clear offer details
- Compelling 'why now' tied to their visit cadence
- Clear call to action
- Under 220 words{extra}"""
    elif "phone" in ch_lower:
        prompt = f"""Write a phone call script for {host_info.get('display_name','Host')} calling {g['name']}.
Offer: {', '.join(offer_summary)}. Guest notes: {g.get('notes','')}.
Talking points: {'; '.join(contact.get('talking_points',[])[:3])}.
Include: 30-sec opening, offer pitch, 2 talking points, objection handling, close.
Conversational tone, not robotic. Under 300 words.{extra}"""
    elif "sms" in ch_lower:
        prompt = f"""Write an SMS from {host_info.get('display_name','Host')} to {g['name']}.
Offer: {', '.join(offer_summary)}.
Under 160 characters, personalized, clear call to action.{extra}"""
    else:
        prompt = f"""Write a personal letter from {host_info.get('display_name','Host')} to {g['name']}.
Offer: {', '.join(offer_summary)}.
Formal, warm, under 200 words.{extra}"""

    if client is None:
        return _fallback_outreach(g, offer_summary, host_info, channel, contact)
    try:
        from google import genai
        return client.models.generate_content(model=_model_id(client), contents=prompt).text
    except Exception as e:
        return _fallback_outreach(g, offer_summary, host_info, channel, contact) + f"\n\n[Gemini: {e}]"

# ── Fallbacks (no API key) ─────────────────────────────────────────────────────

def _fallback_brief(analysis: dict) -> str:
    g = analysis["guest"]; a = analysis["analytics"]; p = analysis["propensity"]
    o = analysis["offer"]; s = analysis["simulation"]; c = analysis["contact"]
    oh = o.get("offer_history_summary", {})
    status = "🔴 LAPSED" if a["days_overdue"]>90 else ("🟡 OVERDUE" if a["days_overdue"]>0 else "🟢 UPCOMING")
    parts = [f"{o[k]['name']} (${o[k].get('cost',0):,})" for k in ["room","food_comp","gaming_comp","show","spa"] if o[k].get("name")]
    hist_note = f"\n**Past offers:** {oh.get('n_offers',0)} offers, {oh.get('accept_rate',0)}% acceptance rate." if oh else ""
    missing = f"\n⚠️ **Missing must-haves:** {', '.join(s['missing_must_haves'])}" if s.get("missing_must_haves") else ""
    return f"""**{status} — {g['name']} ({g['segment']}, {g['tier']})**
Status: {a['days_overdue']} days past their {a['avg_gap_days']}-day cycle. Last seen {a['days_since_last']} days ago.
**Offer:** {' · '.join(parts)}
Total: **${o['total_offer_cost']:,}** ({o['reinvestment_pct']}%) {'✅' if o['within_guardrails'] else '⚠️'}
**Return:** ${s['expected_revenue_if_visit']:,} revenue → **${s['expected_net_if_visit']:,} net** | Accept prob: **{s['accept_probability_pct']}%** (history-adjusted){missing}
**Contact:** {c['primary_channel']} — {c['timing_rule']}
{c['urgency']}{hist_note}"""

def _fallback_rationale(analysis: dict) -> str:
    o = analysis["offer"]; g = analysis["guest"]; a = analysis["analytics"]
    s = analysis["simulation"]; oh = o.get("offer_history_summary", {})
    rat = o.get("rationale", {})
    lines = []
    for k in ["room","nights","food","gaming","show","spa"]:
        if rat.get(k): lines.append(rat[k])
    hist_line = f"Based on {oh.get('n_offers',0)} past offers ({oh.get('accept_rate',0)}% acceptance). {oh.get('recent_declined','')}" if oh else ""
    return " ".join(lines[:4]) + (" " + hist_line if hist_line else "")

def _fallback_refinement_explanation(instruction, old_offer, new_offer) -> str:
    delta = new_offer["total_offer_cost"] - old_offer["total_offer_cost"]
    direction = f"+${delta:,}" if delta >= 0 else f"-${abs(delta):,}"
    return (f"Applied change: \"{instruction}\". "
            f"Total offer went from ${old_offer['total_offer_cost']:,} to ${new_offer['total_offer_cost']:,} ({direction}), "
            f"reinvestment rate {old_offer['reinvestment_pct']}% → {new_offer['reinvestment_pct']}%. "
            f"Guardrail status: {'✅ Within limits' if new_offer['within_guardrails'] else '⚠️ Exceeds cap'}.")

def _fallback_outreach(guest, offer_summary, host_info, channel, contact):
    g = guest
    ch = channel.lower()
    if "email" in ch:
        return f"""**Subject:** A Special Offer Just for You, {g['name'].split()[0]}

Dear {g['name'].split()[0]},

I wanted to personally reach out with an exclusive package for your next visit:
{chr(10).join(f'• {item}' for item in offer_summary)}

It's been a while since we've seen you, and I'd love to welcome you back.

Please reply or call me directly to lock in your dates.

Warm regards,
{host_info.get('display_name','Your Host')}
Host · Kaggle Resort"""
    elif "phone" in ch:
        return f"""**Phone Script — {g['name']}**

**Opening:** "{g['name'].split()[0]}! It's {host_info.get('display_name','your host')} from Kaggle Resort. How have you been? I was thinking about you and wanted to personally reach out."

**Offer pitch:** "I've put together something special: {', '.join(offer_summary)}. I know what you enjoy here and I want to make sure your next trip is exactly right."

**Talking points:**
{chr(10).join(f'• {tp}' for tp in contact.get('talking_points',['Reference their loyalty'])[:3])}

**If hesitant:** "Take your time — but I do want to hold that room for you. Can I follow up in a couple of days?"

**Close:** "What dates work for you?"
"""
    return f"**{channel} — {g['name']}**\nOffer: {', '.join(offer_summary)}\n_Add GEMINI_API_KEY for AI-drafted content._"
