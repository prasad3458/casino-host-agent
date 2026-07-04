# 🎰 Kaggle Resort Host Intelligence Agent

**Google × Kaggle 5-Day AI Agents Vibe Coding Capstone — June 2026**
**Track: Agents for Business**

> A production-ready multi-agent system that helps resort hosts identify overdue guests, build personalized reinvestment offers backed by behavioral history, refine those offers with natural language, simulate ROI, draft outreach content, and manage an approval workflow — all within configurable guardrails and with full host-level access control.

🔗 **Live demo:** [huggingface.co/spaces/prasad3458/casino-host-agent](https://huggingface.co/spaces/prasad3458/casino-host-agent)
🔗 **Source code:** [github.com/prasad3458/casino-host-agent](https://github.com/prasad3458/casino-host-agent)
🔗 **Video walkthrough:** [https://youtu.be/zuhD-MS1hkw](https://youtu.be/zuhD-MS1hkw)

---

## The Problem

Casino hosts at integrated resorts manage portfolios of 200–500 guests. Deciding who to contact, what to offer, and when involves:

- Manually reviewing trip histories across multiple disconnected systems
- Estimating return propensity from intuition rather than data
- Building offers in spreadsheets, often inconsistently applying reinvestment caps
- No simulation of expected return before committing comp budget
- No memory of what worked (or what was declined) for each specific guest

The result: high-value guests lapse because no one noticed their cadence shifted; offers are either too conservative (guests decline) or over-invested (margin erodes).

**The question this agent answers:** *"Who is overdue for a visit, what offer will actually get a yes from this specific guest, and what return should I expect?"*

---

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Gradio UI (app.py)                            │
│  Login · Dashboard · My Guests · Analyze & Refine ·             │
│  Outreach & Load · Host AI Chat · Approvals                     │
│  + live model selector (gemini-2.5-flash / 3.1-flash-lite /      │
│    3.5-flash) at the top of every page                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────────┐
          │   ADK Orchestrator              │  agents/adk_agents.py
          │   (SequentialAgent)             │
          └──┬──────────┬────────┬─────────┘
             │          │        │         │
             ▼          ▼        ▼         ▼
        DataAgent  Propensity OfferAgent Outreach
        (LlmAgent) Agent      (LlmAgent) Agent
                   (LlmAgent)            (LlmAgent)
             │          │        │         │
             └──────────┴────────┴─────────┘
                         │
          ┌──────────────▼──────────────────┐
          │   MCP Server (FastMCP)           │  agents/mcp_server.py
          │   get_guest_profile              │
          │   get_guest_list                 │
          │   get_offer_catalog              │
          │   get_offer_history              │
          │   score_guest_propensity         │
          │   compute_guest_analytics        │
          └──────────────┬──────────────────┘
                         │
          ┌──────────────▼──────────────────┐
          │   Gemini Layer (gemini_agent.py)│
          │   parse_refinement_with_llm()   │  ← reads host's natural
          │     + _enforce_total_language_  │     language, returns a
          │       override() safety net     │     structured plan
          │   chat_with_host()              │
          │   chat_about_portfolio()        │  ← cross-guest reasoning
          │   generate_outreach_content()   │
          └──────────────┬──────────────────┘
                         │
          ┌──────────────▼──────────────────┐
          │   Engine (agents/engine.py)     │
          │   compute_trip_analytics()      │
          │   score_propensity()            │
          │   build_offer()                 │
          │   apply_offer_adjustments()     │  ← deterministically
          │   simulate_roi()                │     EXECUTES the LLM's
          │   analyze_offer_history()       │     plan against the
          └──────────────┬───────────────────┘     real catalog
                         │
          ┌──────────────▼──────────────────┐
          │   Data Layer (read-only)        │
          │   data/guests.py (GUESTS,       │
          │     OFFER_CATALOG, GUARDRAILS,  │
          │     OFFER_HISTORY)              │
          │   data/host_registry.py         │
          │   data/state_store.py  ←writes  │
          └─────────────────────────────────┘
```

### The Natural-Language-to-Execution Boundary

Refining an offer is not regex-driven. When a host types something like *"increase gaming so the total comes to about 6500"* or *"he's worth fighting for, go big on gaming but skip the spa,"* the request goes to `parse_refinement_with_llm()`, which sends Gemini the real catalog prices, the current offer, and the guest's behavioral history, and gets back a structured JSON plan (a specific dollar amount, a target total to solve for, or a component to remove).

That plan — not the host's raw text — is what `apply_offer_adjustments()` executes against the catalog. This split matters for two reasons: the LLM can understand vague or compound phrasing no keyword list could anticipate, and the final dollar figures are always pulled from real catalog entries, never invented by the model. A deterministic safety net (`_enforce_total_language_override`) double-checks the host's literal wording for total-based language and corrects the LLM's plan if its arithmetic disagrees with what was actually asked — this exists because even a capable model will occasionally compute its own (wrong) component figure instead of delegating the math to the system.

### Agent Roles

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| **DataAgent** | Fetch guest profile, analytics, offer history | `tool_fetch_guest_data` |
| **PropensityAgent** | Score return likelihood (0–100), determine quadrant | `tool_score_propensity` |
| **OfferAgent** | Build comp package within guardrails | `tool_build_offer` |
| **OutreachAgent** | Recommend channel, timing, talking points | `tool_recommend_outreach` |
| **Gemini LLM** | Refinement parsing, narrative briefs, rationale, outreach drafts, single-guest chat, portfolio-wide chat | Switchable: `gemini-2.5-flash`, `gemini-3.1-flash-lite`, `gemini-3.5-flash` |

---

## Key Concepts Demonstrated 

| Concept | Where | Implementation |
|---------|-------|----------------|
| **Multi-agent system (ADK)** | `agents/adk_agents.py` | `SequentialAgent` orchestrating 4 `LlmAgent` sub-agents |
| **MCP Server** | `agents/mcp_server.py` | `FastMCP` server with 6 tools exposing guest data and analytics |
| **Agent tools** | `agents/adk_agents.py` | `FunctionTool` wrappers on engine functions; `MCPToolset` pattern |
| **Security features** | `app.py`, `mcp_server.py`, `host_registry.py` | Host-scoped access control, approval thresholds, hard blocks, source immutability |
| **Memory & context** | `data/state_store.py`, session state | `InMemorySessionService` for ADK sessions; offer history as persistent context |
| **Deployability** | `README.md`, `requirements.txt` | HuggingFace Spaces (free CPU, public URL), `.env.example`, no hardcoded keys |

### Course Day Mapping

| Day | Concept | Implementation |
|-----|---------|----------------|
| Day 1 | Vibe coding / autonomous agents | Gemini parses natural-language refinement instructions into structured plans; generates host briefs, rationale, outreach content from natural language |
| Day 2 | Tools & interoperability | MCP server exposes 6 tools; ADK `FunctionTool` and `MCPToolset` pattern; clean LLM-understands / engine-executes boundary |
| Day 3 | Memory & context | `InMemorySessionService` for ADK sessions; offer history as behavioral memory; guest-tagged offer state threaded across tabs; portfolio-wide context summary for cross-guest chat |
| Day 4 | Quality & security | Three-tier guardrail system; host-scoped access control; `copy.deepcopy` source protection; exact guest-identity verification on cached offer state; API key via environment only |
| Day 5 | Prototype to production | HuggingFace Spaces deployment; structured fallbacks when API key absent; live model switching without restart; observability via state_store logs |

---

## Features

### 🤖 Live Model Selector
- Switch between three Gemini models mid-session, no restart needed: `gemini-2.5-flash` (best prose, 20 RPD free), `gemini-3.1-flash-lite` (fastest + strongest benchmarks, 500 RPD free), `gemini-3.5-flash` (newest 3.5 series, 20 RPD free)
- Every AI feature — brief, rationale, refinement parsing, outreach, chat — uses whichever model is currently selected

### 🔐 Host Login & Access Control
- Four demo accounts: `maria.santos`, `james.kowalski`, `rita.bloom`, `supervisor`
- Each host sees only their own portfolio (enforced in MCP server and app)
- Supervisor account sees all guests and manages the approval queue

### 📊 Performance Dashboard
- YTD 2026 vs FY 2025: revenue generated, comp cost, reinvestment rate, trips activated
- Progress bar toward annual revenue target with remaining gap
- Year-over-year percentage change

### 📋 Priority Guest List
- Ranked by cadence overdue × propensity score × avg trip value
- Historical offer acceptance rate per guest (e.g. "75% — 4 offers")
- Best channel identified from history (overrides contact preference when different)

### 🔍 Guest Analysis
- Full trip analytics: avg gap, days overdue, gaming trend, expected return
- Propensity score (0–100) blending recency, frequency, trend, segment, and history
- 2×2 quadrant: propensity × value → offer aggressiveness strategy
- AI host brief (Gemini) covering urgency, offer hook, ROI, and outreach plan

### 📊 Past Offer History
- 57 historical offers (accepted/declined) across all 14 guests
- Per-offer: date, outcome, channel, offer components, dollar total, notes
- Derived insights: acceptance rate, must-have components, minimum gaming threshold, channel rates

### 🧠 History-Aware Offer Construction
- Acceptance probability blends propensity score + historical acceptance rate
- Must-have detection: if gaming/show/spa present in 75%+ of accepted and absent in most declined → flagged as required
- Minimum threshold: if guest declined when gaming was below $X, system won't go below that
- Missing must-haves surface as visible warnings with acceptance probability reduction

### ✏️ Interactive Offer Refinement — Genuinely LLM-Driven
Natural language changes are parsed by Gemini, not regex pattern matching. The model reads the host's raw instruction against the guest's real catalog prices and history and returns a structured plan, which the engine then executes deterministically. This means vague, compound, or never-anticipated phrasing works:
- *"increase gaming to $8000"* (explicit component amount)
- *"increase the total to around 6500"* (target-total — the system solves for the right gaming tier)
- *"he's worth fighting for, go big on gaming but skip the spa"* (vague intent, interpreted using guest history)
- *"remove spa, add Show VIP, 4 nights"* (combined instruction)

Successive refinements compound — adjusting gaming, then later adjusting the show, does not reset the gaming change. Every refined offer is tagged with the exact guest it belongs to, so switching guests mid-session never applies a stale offer to the wrong person. If the live API call fails for any reason, a regex fallback (with the same total-language safeguard) keeps the feature functional in a degraded mode.

Each refinement shows: revised offer, updated acceptance probability, guardrail status, and an AI explanation of the impact.

### 📋 Per-Component Rationale
Every component choice explained with specific data:
- *"Room: High propensity (95/100) — selected top eligible tier (Penthouse Villa)"*
- *"Gaming: History shows minimum $5,000 needed for acceptance. Gaming $8000 selected."*
- *"Show: Present in 75% of accepted offers — must-have for this guest."*
- *"Spa: Guest has no spa history — excluded to preserve budget."*

### ✉️ Outreach Content Generation
- Email with subject line, personalized opening, offer details, call to action
- Phone call script with 30-sec opener, pitch, talking points, objection handling
- SMS under 160 characters
- Personal letter for high-value guests
- Automatically uses the most current offer for the guest — a live refinement if one exists, otherwise the most recently loaded offer, otherwise the default

### 📥 Load Offer to Account
- Writes offer record to `state_store.py` (source data never touched)
- Loads the actual refined/current offer, not a stale rebuilt default
- Guardrail check fires again at load time
- Triggers approval workflow if above guest cap

### ✅ Three-Tier Approval System
- **Within guest cap**: load directly
- **Between guest cap and hard cap**: submit for supervisor approval with reason — available directly from the Analyze & Refine tab as well as Outreach & Load
- **Above hard cap**: hard block — cannot proceed regardless of who asks
- Supervisor approves/rejects from a dropdown of pending requests (no manual ID entry); approved offers auto-load

### 💬 Host AI Chat — Single Guest or Whole Portfolio
A mode toggle switches the chat between two scopes:
- **This Guest** — multi-turn conversation grounded in the analyzed guest's full context (offer, history, rationale). Automatically uses the most current offer (live refinement → last loaded offer → default), so questions like *"what's the last offer loaded?"* get an accurate answer.
- **My Whole Portfolio** — reasons over every guest in the host's book at once: *"who should I call first this week?"*, *"which guest has the best acceptance rate?"*, *"compare Derek and Marcus"*. Built from a compact per-guest summary table plus this session's loaded offers and pending approvals, so answers are grounded in the same numbers visible elsewhere in the app.

---

## Project Structure

```
casino-host-agent/
├── app.py                    # Gradio UI — all 8 tabs, model selector, state consistency logic
├── requirements.txt          # Python dependencies
├── .env.example               # Environment variable template (never commit .env)
├── .gitignore
│
├── agents/
│   ├── __init__.py
│   ├── engine.py             # Core analytics: propensity, offer building, simulation, refinement execution
│   ├── gemini_agent.py       # Gemini integration: refinement parsing, briefs, rationale, outreach, single + portfolio chat
│   ├── adk_agents.py         # ADK multi-agent system: 4 LlmAgents + SequentialAgent
│   └── mcp_server.py         # MCP server: 6 tools via FastMCP (stdio transport)
│
└── data/
    ├── __init__.py
    ├── guests.py             # Synthetic guest data (READ-ONLY at runtime)
                              # GUESTS, OFFER_CATALOG, GUARDRAILS, OFFER_HISTORY
    ├── host_registry.py      # Host credentials, approval thresholds (READ-ONLY)
    └── state_store.py        # Runtime writes ONLY — approvals, loaded offers, logs
```

**Data protection guarantee:** `guests.py` and `host_registry.py` are never mutated at runtime. All writes go exclusively to `state_store.py`. Offer snapshots use `copy.deepcopy()` to prevent reference mutation.

**Offer state consistency guarantee:** every tab that references "the current offer" for a guest — Outreach drafting, Load to Account, and Host AI Chat — resolves it through the same priority chain: an in-progress refinement for that exact guest (verified by an exact `_guest_id` tag, not a heuristic), falling back to the most recently loaded offer from `state_store`, falling back to the freshly-built default. No tab independently rebuilds its own stale copy.

---

## Setup & Deployment

### Local Development

```bash
git clone https://github.com/prasad3458/casino-host-agent
cd casino-host-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment (never commit this file)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Optionally override the default model (gemini-2.5-flash):
# export GEMINI_MODEL=gemini-3.1-flash-lite

# Run
python app.py
# Open http://localhost:7860
```

**The app works fully without a Gemini API key** — all analytics, offer recommendations, simulation, and offer history work via the engine. The key only adds AI-generated briefs, rationale paragraphs, refinement parsing (falls back to a regex parser), outreach content, and chat. The model selector in the UI lets you switch between `gemini-2.5-flash`, `gemini-3.1-flash-lite`, and `gemini-3.5-flash` at any time without restarting.

### Run the ADK Pipeline (standalone)

```bash
# Set your API key first
export GEMINI_API_KEY=your_key

# Run the full 4-agent pipeline for a guest
python agents/adk_agents.py --guest G005 --host james.kowalski

# Run the MCP server standalone (stdio transport)
python agents/mcp_server.py
```

### Deploy to HuggingFace Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
   - SDK: **Gradio** · Hardware: **Free CPU** · Visibility: **Public**
2. Upload all files maintaining the `data/` and `agents/` folder structure
3. Add `GEMINI_API_KEY` as a **Space Secret** (Settings → Variables and Secrets)
   - Never paste the key directly in code or commit it
4. Optionally add `GEMINI_MODEL` as a regular **Variable** (not a secret) to change the default model without code changes
5. Space builds automatically in ~2–4 minutes
6. Public URL: `https://huggingface.co/spaces/prasad3458/casino-host-agent`

### Demo Accounts

| Username | Password | Portfolio |
|----------|----------|-----------|
| `maria.santos` | `maria2026` | Whales (Richard Harmon, Linda Zhao) + High Roller + Premium |
| `james.kowalski` | `james2026` | High Rollers (Marcus Webb, Priya Nair, Derek Fontaine) + Premium |
| `rita.bloom` | `rita2026` | Premium + Mid-tier + Developing (6 guests) |
| `supervisor` | `super2026` | All 14 guests · Approval queue access |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Gemini, switchable live: `gemini-2.5-flash` / `gemini-3.1-flash-lite` / `gemini-3.5-flash` (Google AI Studio) |
| Agent Framework | Google ADK 2.3.0 (`SequentialAgent`, `LlmAgent`, `FunctionTool`) |
| MCP Server | FastMCP (`mcp` 1.28.x, stdio transport) |
| UI & Hosting | Gradio 6.x on HuggingFace Spaces (free CPU tier) |
| Data | Bundled synthetic Python dicts — no external database |
| Memory | `InMemorySessionService` (ADK) + Python in-memory state store + guest-tagged offer state in Gradio session |

---

## Security Design

1. **No hardcoded credentials**: API key via environment variable only (`GEMINI_API_KEY`)
2. **Host-scoped access control**: enforced at both the MCP tool level and the Gradio app level
3. **Three-tier guardrails**: guest cap → supervisor approval → hard block
4. **Source data immutability**: `guests.py` and `host_registry.py` never written at runtime; all writes go to `state_store.py`; offer snapshots use `copy.deepcopy()`
5. **Exact guest-identity tagging on offer state**: every refined offer carries a `_guest_id` tag, checked exactly (not heuristically) before being trusted by Outreach, Load, or Chat — this prevents one guest's customized offer from accidentally being applied to a different guest selected later in the same session
6. **No PII**: all guest data is synthetic — no real guest information used

---

## Data Notes

All guest profiles, trip histories, and offer history records are **synthetic** — generated to reflect realistic casino hospitality patterns. The offer catalog, reinvestment caps, and guardrail thresholds are based on publicly discussed industry norms, not proprietary Kaggle Resort data.

57 historical offer records across 14 guests: each with date, outcome (Accepted/Declined), channel, offer components, total cost, and notes explaining the acceptance or decline reason.

---

## What's Next (Production Path)

- Connect to real CRM/PMS APIs (SevenRooms, LMS, Hotel PMS) via secure MCP tools replacing the bundled synthetic data
- Persistent session store (Cloud Firestore or BigQuery) replacing `InMemorySessionService`
- A/B test offer strategies across guest cohorts via the ADK evaluation framework
- Offer acceptance feedback loop: when a guest accepts or declines, update propensity model weights
- Natural language offer drafting integrated into the approval workflow

---

*Built for the Google × Kaggle 5-Day AI Agents Vibe Coding Intensive, June 2026*
