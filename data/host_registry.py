"""
Host registry and access control.
Source data (HOSTS, HOST_CREDENTIALS) is NEVER mutated at runtime.
All session state lives in the app layer.
"""

# ── Host definitions (read-only source data) ─────────────────────────────────
HOSTS = {
    "maria.santos": {
        "display_name": "Maria Santos",
        "title": "Senior Resort Host",
        "password": "maria2026",       # demo only — real app uses hashed auth
        "supervisor": False,
        "ytd_revenue_target": 1_200_000,
    },
    "james.kowalski": {
        "display_name": "James Kowalski",
        "title": "Resort Host",
        "password": "james2026",
        "supervisor": False,
        "ytd_revenue_target": 800_000,
    },
    "rita.bloom": {
        "display_name": "Rita Bloom",
        "title": "Resort Host",
        "password": "rita2026",
        "supervisor": False,
        "ytd_revenue_target": 400_000,
    },
    "supervisor": {
        "display_name": "VP Player Development",
        "title": "Supervisor",
        "password": "super2026",
        "supervisor": True,
        "ytd_revenue_target": None,
    },
}

# ── Guest-to-host mapping (derived from GUESTS, never mutated) ───────────────
# Maps display name in guest['host'] → login key
HOST_NAME_TO_KEY = {
    "Maria Santos":   "maria.santos",
    "James Kowalski": "james.kowalski",
    "Rita Bloom":     "rita.bloom",
}

# ── Approval thresholds ───────────────────────────────────────────────────────
# If offer reinvestment % is between cap and this threshold → auto-flag for approval
# If above threshold → hard block, supervisor must override
APPROVAL_THRESHOLDS = {
    "Developing":   {"soft_cap_pct": 0.22, "hard_cap_pct": 0.30},
    "Mid-tier":     {"soft_cap_pct": 0.20, "hard_cap_pct": 0.28},
    "Premium":      {"soft_cap_pct": 0.25, "hard_cap_pct": 0.32},
    "High Roller":  {"soft_cap_pct": 0.30, "hard_cap_pct": 0.38},
    "Whale":        {"soft_cap_pct": 0.35, "hard_cap_pct": 0.45},
}
# soft_cap_pct  = per-guest cap (from guests.py) — host can submit for approval above this
# hard_cap_pct  = absolute maximum — supervisor-only override, cannot be self-approved
