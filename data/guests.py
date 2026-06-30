"""
Synthetic Kaggle Resort guest data — read-only source data.
NEVER mutate this at runtime. All writes go to state_store.py.

Segments: Whale, High Roller, Premium, Mid-tier, Developing
Hosts: Maria Santos (G001-G004), James Kowalski (G005-G008), Rita Bloom (G009-G014)
"""

GUESTS = [
    # ══ MARIA SANTOS PORTFOLIO ══════════════════════════════════════════════
    {
        "id": "G001", "name": "Richard Harmon", "age": 58, "city": "San Francisco, CA",
        "segment": "Whale", "tier": "Noir", "contact_pref": ["Phone", "Personal Letter"],
        "host": "Maria Santos",
        "trips": [
            {"date": "2021-03-12", "nights": 4, "room": "Signature Villa", "gaming_win_loss": -48200, "food_spend": 3100, "show_spend": 800, "spa_spend": 600, "offers_redeemed": ["Villa Comp", "F&B $1500"]},
            {"date": "2021-09-08", "nights": 3, "room": "Penthouse Villa",   "gaming_win_loss": -61500, "food_spend": 2800, "show_spend": 1200, "spa_spend": 0,   "offers_redeemed": ["Penthouse Villa Comp", "Show Tickets x4"]},
            {"date": "2022-02-19", "nights": 5, "room": "Signature Villa", "gaming_win_loss":  12400, "food_spend": 4200, "show_spend": 0,    "spa_spend": 900, "offers_redeemed": ["Villa Comp", "F&B $2000"]},
            {"date": "2022-08-14", "nights": 4, "room": "Penthouse Villa",   "gaming_win_loss": -73100, "food_spend": 3600, "show_spend": 600,  "spa_spend": 0,   "offers_redeemed": ["Penthouse Villa Comp", "Gaming $5000"]},
            {"date": "2023-01-27", "nights": 3, "room": "Signature Villa", "gaming_win_loss": -55900, "food_spend": 2900, "show_spend": 900,  "spa_spend": 300, "offers_redeemed": ["Villa Comp", "F&B $1500"]},
            {"date": "2023-07-03", "nights": 5, "room": "Penthouse Villa",   "gaming_win_loss": -88400, "food_spend": 4800, "show_spend": 1400, "spa_spend": 0,   "offers_redeemed": ["Penthouse Villa Comp", "Gaming $8000", "Show VIP"]},
            {"date": "2024-02-11", "nights": 4, "room": "Signature Villa", "gaming_win_loss": -42300, "food_spend": 3300, "show_spend": 500,  "spa_spend": 700, "offers_redeemed": ["Villa Comp", "F&B $2000"]},
            {"date": "2024-09-22", "nights": 3, "room": "Penthouse Villa",   "gaming_win_loss": -67800, "food_spend": 2700, "show_spend": 0,    "spa_spend": 0,   "offers_redeemed": ["Penthouse Villa Comp", "Gaming $6000"]},
            {"date": "2025-04-05", "nights": 4, "room": "Signature Villa", "gaming_win_loss": -71200, "food_spend": 3500, "show_spend": 800,  "spa_spend": 600, "offers_redeemed": ["Villa Comp", "F&B $2000", "Show VIP"]},
            {"date": "2025-10-18", "nights": 3, "room": "Penthouse Villa",   "gaming_win_loss": -59400, "food_spend": 2900, "show_spend": 0,    "spa_spend": 0,   "offers_redeemed": ["Penthouse Villa Comp", "Gaming $8000"]},
        ],
        "last_visit": "2026-03-15",
        "ytd_trips_2026": [
            {"date": "2026-03-15", "gaming_win_loss": -64300, "food_spend": 3200, "show_spend": 600, "spa_spend": 400, "comp_cost": 18500},
        ],
        "ytd_trips_2025": [
            {"date": "2025-04-05", "gaming_win_loss": -71200, "food_spend": 3500, "show_spend": 800, "spa_spend": 600, "comp_cost": 19000},
            {"date": "2025-10-18", "gaming_win_loss": -59400, "food_spend": 2900, "show_spend": 0,   "spa_spend": 0,   "comp_cost": 16500},
        ],
        "avg_visits_per_year": 2.3, "avg_trip_gaming_loss": 54700, "avg_trip_total_spend": 62100,
        "notes": "Prefers Baccarat. Always requests north-facing villa. Wife accompanies — book spa package. Never responds to email.",
        "reinvestment_cap_pct": 0.35,
    },
    {
        "id": "G002", "name": "Linda Zhao", "age": 52, "city": "Los Angeles, CA",
        "segment": "Whale", "tier": "Noir", "contact_pref": ["Phone", "Email"],
        "host": "Maria Santos",
        "trips": [
            {"date": "2021-05-18", "nights": 3, "room": "Grand Suite", "gaming_win_loss": -39100, "food_spend": 2400, "show_spend": 1100, "spa_spend": 1800, "offers_redeemed": ["Suite Comp", "Spa Package"]},
            {"date": "2021-11-02", "nights": 2, "room": "Kaggle Suite", "gaming_win_loss": -28700, "food_spend": 1600, "show_spend": 600,  "spa_spend": 2200, "offers_redeemed": ["Suite Comp", "F&B $800"]},
            {"date": "2022-04-09", "nights": 3, "room": "Grand Suite", "gaming_win_loss": -51300, "food_spend": 2900, "show_spend": 0,    "spa_spend": 2400, "offers_redeemed": ["Suite Comp", "Spa $500", "Gaming $3000"]},
            {"date": "2022-10-22", "nights": 3, "room": "Grand Suite", "gaming_win_loss": -44600, "food_spend": 2200, "show_spend": 800,  "spa_spend": 1900, "offers_redeemed": ["Suite Comp", "F&B $1200"]},
            {"date": "2023-03-14", "nights": 4, "room": "Signature Villa",   "gaming_win_loss": -58200, "food_spend": 3100, "show_spend": 1400, "spa_spend": 2700, "offers_redeemed": ["Villa Comp", "Spa Package", "Show x2"]},
            {"date": "2023-09-28", "nights": 2, "room": "Kaggle Suite", "gaming_win_loss": -31400, "food_spend": 1800, "show_spend": 900,  "spa_spend": 2100, "offers_redeemed": ["Suite Comp", "F&B $1000"]},
            {"date": "2024-04-16", "nights": 3, "room": "Grand Suite", "gaming_win_loss": -47900, "food_spend": 2600, "show_spend": 0,    "spa_spend": 2800, "offers_redeemed": ["Suite Comp", "Spa $600", "Gaming $3500"]},
            {"date": "2024-11-08", "nights": 3, "room": "Signature Villa",   "gaming_win_loss": -52100, "food_spend": 2800, "show_spend": 1200, "spa_spend": 2500, "offers_redeemed": ["Villa Comp", "Spa Package", "Show x2"]},
            {"date": "2025-05-22", "nights": 2, "room": "Grand Suite", "gaming_win_loss": -38600, "food_spend": 2100, "show_spend": 800,  "spa_spend": 2200, "offers_redeemed": ["Suite Comp", "Spa $500"]},
        ],
        "last_visit": "2025-12-10",
        "ytd_trips_2026": [],
        "ytd_trips_2025": [
            {"date": "2025-05-22", "gaming_win_loss": -38600, "food_spend": 2100, "show_spend": 800, "spa_spend": 2200, "comp_cost": 14200},
            {"date": "2025-12-10", "gaming_win_loss": -44900, "food_spend": 2400, "show_spend": 0,   "spa_spend": 2400, "comp_cost": 15500},
        ],
        "avg_visits_per_year": 2.1, "avg_trip_gaming_loss": 43040, "avg_trip_total_spend": 52340,
        "notes": "High spa spend — always books Summit Spa. Prefers slots and Pai Gow. Responds well to spa + show combo offers.",
        "reinvestment_cap_pct": 0.38,
    },
    {
        "id": "G003", "name": "Victor Castellano", "age": 61, "city": "Miami, FL",
        "segment": "High Roller", "tier": "Titanium", "contact_pref": ["Phone"],
        "host": "Maria Santos",
        "trips": [
            {"date": "2021-08-03", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -19800, "food_spend": 1600, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 2N", "F&B $800"]},
            {"date": "2022-03-17", "nights": 4, "room": "Grand Suite", "gaming_win_loss": -27300, "food_spend": 2100, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp", "Gaming $2000"]},
            {"date": "2022-11-09", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -21600, "food_spend": 1800, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 3N", "Gaming $1500"]},
            {"date": "2023-06-21", "nights": 4, "room": "Grand Suite", "gaming_win_loss": -33400, "food_spend": 2500, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp", "F&B $1200", "Gaming $2500"]},
            {"date": "2024-01-15", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -24100, "food_spend": 1900, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 3N", "Gaming $2000"]},
            {"date": "2024-08-29", "nights": 4, "room": "Grand Suite", "gaming_win_loss": -29700, "food_spend": 2300, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp", "Gaming $2000"]},
            {"date": "2025-03-12", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -22800, "food_spend": 1700, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 3N", "Gaming $2000"]},
        ],
        "last_visit": "2026-01-08",
        "ytd_trips_2026": [
            {"date": "2026-01-08", "gaming_win_loss": -26400, "food_spend": 2000, "show_spend": 0, "spa_spend": 0, "comp_cost": 6200},
        ],
        "ytd_trips_2025": [
            {"date": "2025-03-12", "gaming_win_loss": -22800, "food_spend": 1700, "show_spend": 0, "spa_spend": 0, "comp_cost": 5800},
            {"date": "2025-09-04", "gaming_win_loss": -31200, "food_spend": 2200, "show_spend": 0, "spa_spend": 0, "comp_cost": 7500},
        ],
        "avg_visits_per_year": 1.8, "avg_trip_gaming_loss": 25529, "avg_trip_total_spend": 29129,
        "notes": "Pure gaming — Craps and Baccarat. Never uses amenities. Only phone. Suite comp + gaming match play is the only offer that works.",
        "reinvestment_cap_pct": 0.28,
    },
    {
        "id": "G004", "name": "Natasha Brennan", "age": 47, "city": "New York, NY",
        "segment": "Premium", "tier": "Platinum", "contact_pref": ["Email", "Phone"],
        "host": "Maria Santos",
        "trips": [
            {"date": "2022-06-11", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -6800, "food_spend": 700, "show_spend": 500, "spa_spend": 400, "offers_redeemed": ["Room Comp 1N", "F&B $300"]},
            {"date": "2023-01-08", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -9200, "food_spend": 900, "show_spend": 700, "spa_spend": 550, "offers_redeemed": ["Room Comp 2N", "Show x2", "Spa $200"]},
            {"date": "2023-07-19", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -7400, "food_spend": 750, "show_spend": 600, "spa_spend": 480, "offers_redeemed": ["Room Comp 2N", "F&B $300"]},
            {"date": "2024-02-05", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -10800,"food_spend": 950, "show_spend": 800, "spa_spend": 600, "offers_redeemed": ["Room Comp 3N", "Gaming $800", "Show x2"]},
            {"date": "2024-09-14", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -8100, "food_spend": 800, "show_spend": 500, "spa_spend": 520, "offers_redeemed": ["Room Comp 2N", "Spa $200"]},
            {"date": "2025-04-28", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -11400,"food_spend": 1000,"show_spend": 750, "spa_spend": 600, "offers_redeemed": ["Room Comp 3N", "Gaming $1000", "Show x2"]},
        ],
        "last_visit": "2026-05-02",
        "ytd_trips_2026": [
            {"date": "2026-05-02", "gaming_win_loss": -9600, "food_spend": 880, "show_spend": 650, "spa_spend": 520, "comp_cost": 2800},
        ],
        "ytd_trips_2025": [
            {"date": "2025-04-28", "gaming_win_loss": -11400, "food_spend": 1000, "show_spend": 750, "spa_spend": 600, "comp_cost": 3200},
            {"date": "2025-11-15", "gaming_win_loss": -8900, "food_spend": 820, "show_spend": 600, "spa_spend": 500, "comp_cost": 2600},
        ],
        "avg_visits_per_year": 1.8, "avg_trip_gaming_loss": 8917, "avg_trip_total_spend": 11367,
        "notes": "NY attorney, flies in quarterly. Enjoys shows and spa. Slots and Roulette. Responds to email with detailed offer breakdown.",
        "reinvestment_cap_pct": 0.26,
    },

    # ══ JAMES KOWALSKI PORTFOLIO ════════════════════════════════════════════
    {
        "id": "G005", "name": "Marcus Webb", "age": 45, "city": "Houston, TX",
        "segment": "High Roller", "tier": "Titanium", "contact_pref": ["Email", "Phone"],
        "host": "James Kowalski",
        "trips": [
            {"date": "2021-06-20", "nights": 3, "room": "Luxury King",  "gaming_win_loss": -12400, "food_spend": 900, "show_spend": 400, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "F&B $400"]},
            {"date": "2021-12-10", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -8900,  "food_spend": 600, "show_spend": 0,   "spa_spend": 0, "offers_redeemed": ["Room $150/N", "Gaming $500"]},
            {"date": "2022-05-28", "nights": 3, "room": "Luxury King",  "gaming_win_loss": -15600, "food_spend": 1100,"show_spend": 600, "spa_spend": 0, "offers_redeemed": ["Room Comp 3N", "F&B $600"]},
            {"date": "2022-11-14", "nights": 2, "room": "Kaggle King", "gaming_win_loss": -11200, "food_spend": 800, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Show x2"]},
            {"date": "2023-04-08", "nights": 3, "room": "Luxury King",  "gaming_win_loss": -18300, "food_spend": 1300,"show_spend": 400, "spa_spend": 0, "offers_redeemed": ["Room Comp 3N", "Gaming $1500", "F&B $700"]},
            {"date": "2023-10-19", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -9800,  "food_spend": 700, "show_spend": 500, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "F&B $400"]},
            {"date": "2024-03-07", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -14100, "food_spend": 1000,"show_spend": 0,   "spa_spend": 0, "offers_redeemed": ["Room Comp 3N", "Gaming $1000"]},
            {"date": "2024-10-31", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -10600, "food_spend": 750, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N"]},
            {"date": "2025-05-14", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -16800, "food_spend": 1100,"show_spend": 400, "spa_spend": 0, "offers_redeemed": ["Room Comp 3N", "Gaming $1500"]},
            {"date": "2025-11-22", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -11900, "food_spend": 820, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $1000"]},
        ],
        "last_visit": "2026-05-10",
        "ytd_trips_2026": [
            {"date": "2026-05-10", "gaming_win_loss": -14200, "food_spend": 950, "show_spend": 350, "spa_spend": 0, "comp_cost": 4100},
        ],
        "ytd_trips_2025": [
            {"date": "2025-05-14", "gaming_win_loss": -16800, "food_spend": 1100, "show_spend": 400, "spa_spend": 0, "comp_cost": 4800},
            {"date": "2025-11-22", "gaming_win_loss": -11900, "food_spend": 820,  "show_spend": 300, "spa_spend": 0, "comp_cost": 3600},
        ],
        "avg_visits_per_year": 2.4, "avg_trip_gaming_loss": 12613, "avg_trip_total_spend": 15363,
        "notes": "Strictly Blackjack. Never uses spa. Responds to gaming match play offers. Prefers email outreach.",
        "reinvestment_cap_pct": 0.30,
    },
    {
        "id": "G006", "name": "Priya Nair", "age": 39, "city": "Chicago, IL",
        "segment": "High Roller", "tier": "Titanium", "contact_pref": ["Email"],
        "host": "James Kowalski",
        "trips": [
            {"date": "2021-08-14", "nights": 2, "room": "Kaggle Queen", "gaming_win_loss": -9600,  "food_spend": 700, "show_spend": 500, "spa_spend": 400, "offers_redeemed": ["Room $120/N", "F&B $300"]},
            {"date": "2022-01-29", "nights": 3, "room": "Luxury King",   "gaming_win_loss": -13800, "food_spend": 1000,"show_spend": 800, "spa_spend": 600, "offers_redeemed": ["Room Comp 2N", "Show x2", "Spa $200"]},
            {"date": "2022-07-07", "nights": 2, "room": "Kaggle Queen", "gaming_win_loss": -8200,  "food_spend": 650, "show_spend": 400, "spa_spend": 350, "offers_redeemed": ["Room $120/N", "F&B $300"]},
            {"date": "2023-02-18", "nights": 3, "room": "Luxury King",   "gaming_win_loss": -16400, "food_spend": 1100,"show_spend": 600, "spa_spend": 500, "offers_redeemed": ["Room Comp 3N", "Gaming $1200", "Show x2"]},
            {"date": "2023-08-25", "nights": 2, "room": "Kaggle Queen", "gaming_win_loss": -10900, "food_spend": 800, "show_spend": 700, "spa_spend": 400, "offers_redeemed": ["Room Comp 2N", "F&B $400"]},
            {"date": "2024-01-13", "nights": 3, "room": "Luxury King",   "gaming_win_loss": -14700, "food_spend": 950, "show_spend": 500, "spa_spend": 550, "offers_redeemed": ["Room Comp 3N", "Spa $250", "Gaming $1000"]},
            {"date": "2024-07-20", "nights": 2, "room": "Kaggle Queen", "gaming_win_loss": -11300, "food_spend": 750, "show_spend": 600, "spa_spend": 450, "offers_redeemed": ["Room Comp 2N", "Show x2"]},
            {"date": "2025-02-09", "nights": 3, "room": "Luxury King",   "gaming_win_loss": -15600, "food_spend": 1000,"show_spend": 700, "spa_spend": 500, "offers_redeemed": ["Room Comp 3N", "Gaming $1200"]},
            {"date": "2025-09-18", "nights": 2, "room": "Kaggle Queen", "gaming_win_loss": -12100, "food_spend": 800, "show_spend": 600, "spa_spend": 450, "offers_redeemed": ["Room Comp 2N", "Show x2"]},
        ],
        "last_visit": "2026-02-10",
        "ytd_trips_2026": [
            {"date": "2026-02-10", "gaming_win_loss": -13800, "food_spend": 920, "show_spend": 600, "spa_spend": 480, "comp_cost": 4200},
        ],
        "ytd_trips_2025": [
            {"date": "2025-02-09", "gaming_win_loss": -15600, "food_spend": 1000, "show_spend": 700, "spa_spend": 500, "comp_cost": 4600},
            {"date": "2025-09-18", "gaming_win_loss": -12100, "food_spend": 800,  "show_spend": 600, "spa_spend": 450, "comp_cost": 3800},
        ],
        "avg_visits_per_year": 2.0, "avg_trip_gaming_loss": 12129, "avg_trip_total_spend": 14979,
        "notes": "Enjoys shows and spa. Craps and Roulette. Travels with friend group — extra room comps increase acceptance rate.",
        "reinvestment_cap_pct": 0.32,
    },
    {
        "id": "G007", "name": "Derek Fontaine", "age": 63, "city": "Dallas, TX",
        "segment": "High Roller", "tier": "Titanium", "contact_pref": ["Phone"],
        "host": "James Kowalski",
        "trips": [
            {"date": "2020-11-08", "nights": 4, "room": "Kaggle Suite", "gaming_win_loss": -21400, "food_spend": 1800, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 3N", "F&B $800"]},
            {"date": "2021-04-22", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -17200, "food_spend": 1400, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 2N", "Gaming $1500"]},
            {"date": "2022-02-14", "nights": 4, "room": "Grand Suite", "gaming_win_loss": -28900, "food_spend": 2200, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp", "F&B $1000", "Gaming $2000"]},
            {"date": "2023-03-19", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -19600, "food_spend": 1600, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 3N", "Gaming $1500"]},
            {"date": "2023-11-27", "nights": 4, "room": "Grand Suite", "gaming_win_loss": -24100, "food_spend": 2000, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp", "F&B $900", "Gaming $2000"]},
            {"date": "2024-07-08", "nights": 3, "room": "Kaggle Suite", "gaming_win_loss": -22600, "food_spend": 1900, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Suite Comp 3N", "Gaming $2000"]},
        ],
        "last_visit": "2025-06-15",
        "ytd_trips_2026": [],
        "ytd_trips_2025": [
            {"date": "2025-06-15", "gaming_win_loss": -26100, "food_spend": 2100, "show_spend": 0, "spa_spend": 0, "comp_cost": 6800},
        ],
        "avg_visits_per_year": 1.1, "avg_trip_gaming_loss": 22240, "avg_trip_total_spend": 25840,
        "notes": "Visits less frequently but extremely high value. Pure gaming — no spa/shows. Suite + gaming match play combo always converts. LAPSED — 12 months since last visit.",
        "reinvestment_cap_pct": 0.28,
    },
    {
        "id": "G008", "name": "Carlos Reyes", "age": 54, "city": "San Antonio, TX",
        "segment": "Premium", "tier": "Platinum", "contact_pref": ["Phone", "Email"],
        "host": "James Kowalski",
        "trips": [
            {"date": "2022-04-14", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -5600, "food_spend": 600, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "F&B $250"]},
            {"date": "2022-11-03", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -7200, "food_spend": 700, "show_spend": 400, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $500"]},
            {"date": "2023-05-20", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -9400, "food_spend": 900, "show_spend": 500, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "F&B $400", "Gaming $600"]},
            {"date": "2023-12-09", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -6800, "food_spend": 680, "show_spend": 350, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $500"]},
            {"date": "2024-06-28", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -10200,"food_spend": 950, "show_spend": 450, "spa_spend": 0, "offers_redeemed": ["Room Comp 3N", "Gaming $800"]},
            {"date": "2025-01-17", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -7600, "food_spend": 720, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $600"]},
            {"date": "2025-08-05", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -11100,"food_spend": 980, "show_spend": 500, "spa_spend": 0, "offers_redeemed": ["Room Comp 3N", "Gaming $1000"]},
        ],
        "last_visit": "2026-03-22",
        "ytd_trips_2026": [
            {"date": "2026-03-22", "gaming_win_loss": -8900, "food_spend": 840, "show_spend": 380, "spa_spend": 0, "comp_cost": 2600},
        ],
        "ytd_trips_2025": [
            {"date": "2025-01-17", "gaming_win_loss": -7600,  "food_spend": 720, "show_spend": 300, "spa_spend": 0, "comp_cost": 2200},
            {"date": "2025-08-05", "gaming_win_loss": -11100, "food_spend": 980, "show_spend": 500, "spa_spend": 0, "comp_cost": 3000},
        ],
        "avg_visits_per_year": 2.0, "avg_trip_gaming_loss": 8271, "avg_trip_total_spend": 9921,
        "notes": "Loyal mid-premium guest. Slots and video poker. Responds to phone first, then email. Never spa.",
        "reinvestment_cap_pct": 0.24,
    },

    # ══ RITA BLOOM PORTFOLIO ════════════════════════════════════════════════
    {
        "id": "G009", "name": "Angela Torres", "age": 44, "city": "Phoenix, AZ",
        "segment": "Premium", "tier": "Platinum", "contact_pref": ["Email", "SMS"],
        "host": "Rita Bloom",
        "trips": [
            {"date": "2021-07-10", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -3800, "food_spend": 400, "show_spend": 300, "spa_spend": 200, "offers_redeemed": ["Room $89/N", "F&B $150"]},
            {"date": "2022-01-22", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -5200, "food_spend": 550, "show_spend": 0,   "spa_spend": 250, "offers_redeemed": ["Room Comp 1N", "F&B $200"]},
            {"date": "2022-08-05", "nights": 3, "room": "Deluxe King",  "gaming_win_loss": -4600, "food_spend": 480, "show_spend": 300, "spa_spend": 180, "offers_redeemed": ["Room $89/N", "Show x1"]},
            {"date": "2023-02-17", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -6100, "food_spend": 600, "show_spend": 200, "spa_spend": 300, "offers_redeemed": ["Room Comp 2N", "F&B $250", "Spa $100"]},
            {"date": "2023-09-01", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -3900, "food_spend": 420, "show_spend": 350, "spa_spend": 200, "offers_redeemed": ["Room $89/N", "Show x1"]},
            {"date": "2024-03-28", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -7200, "food_spend": 700, "show_spend": 400, "spa_spend": 350, "offers_redeemed": ["Room Comp 2N", "F&B $300", "Gaming $400"]},
            {"date": "2024-11-14", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -5600, "food_spend": 560, "show_spend": 350, "spa_spend": 280, "offers_redeemed": ["Room Comp 2N", "Show x1"]},
            {"date": "2025-06-08", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -7800, "food_spend": 720, "show_spend": 450, "spa_spend": 320, "offers_redeemed": ["Room Comp 2N", "F&B $300", "Show x1"]},
        ],
        "last_visit": "2026-05-28",
        "ytd_trips_2026": [
            {"date": "2026-05-28", "gaming_win_loss": -6400, "food_spend": 640, "show_spend": 380, "spa_spend": 260, "comp_cost": 1900},
        ],
        "ytd_trips_2025": [
            {"date": "2025-06-08", "gaming_win_loss": -7800, "food_spend": 720, "show_spend": 450, "spa_spend": 320, "comp_cost": 2200},
            {"date": "2025-12-19", "gaming_win_loss": -5900, "food_spend": 580, "show_spend": 300, "spa_spend": 240, "comp_cost": 1700},
        ],
        "avg_visits_per_year": 1.7, "avg_trip_gaming_loss": 5133, "avg_trip_total_spend": 6483,
        "notes": "Consistent visitor, responds well to email. Mix of slots and table games. Appreciates show offers.",
        "reinvestment_cap_pct": 0.25,
    },
    {
        "id": "G010", "name": "Kevin Park", "age": 37, "city": "Seattle, WA",
        "segment": "Premium", "tier": "Platinum", "contact_pref": ["Email"],
        "host": "Rita Bloom",
        "trips": [
            {"date": "2022-03-11", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -4100, "food_spend": 450, "show_spend": 200, "spa_spend": 0, "offers_redeemed": ["Room $99/N"]},
            {"date": "2022-09-24", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -5800, "food_spend": 600, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "F&B $200"]},
            {"date": "2023-04-15", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -7300, "food_spend": 750, "show_spend": 400, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $500"]},
            {"date": "2023-11-08", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -4900, "food_spend": 500, "show_spend": 250, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "F&B $200", "Show x1"]},
            {"date": "2024-06-02", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -6600, "food_spend": 680, "show_spend": 350, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $500"]},
            {"date": "2025-01-29", "nights": 2, "room": "Luxury King",  "gaming_win_loss": -5400, "food_spend": 560, "show_spend": 280, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Gaming $400"]},
            {"date": "2025-09-11", "nights": 3, "room": "Kaggle King", "gaming_win_loss": -7800, "food_spend": 780, "show_spend": 400, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "Gaming $600"]},
        ],
        "last_visit": "2026-04-20",
        "ytd_trips_2026": [
            {"date": "2026-04-20", "gaming_win_loss": -7100, "food_spend": 720, "show_spend": 350, "spa_spend": 0, "comp_cost": 2100},
        ],
        "ytd_trips_2025": [
            {"date": "2025-01-29", "gaming_win_loss": -5400, "food_spend": 560, "show_spend": 280, "spa_spend": 0, "comp_cost": 1600},
            {"date": "2025-09-11", "gaming_win_loss": -7800, "food_spend": 780, "show_spend": 400, "spa_spend": 0, "comp_cost": 2200},
        ],
        "avg_visits_per_year": 1.5, "avg_trip_gaming_loss": 5740, "avg_trip_total_spend": 7420,
        "notes": "Tech professional, methodical. Blackjack only. Never uses spa. Responds only to email with clear offer value.",
        "reinvestment_cap_pct": 0.22,
    },
    {
        "id": "G011", "name": "Sandra Mitchell", "age": 56, "city": "Denver, CO",
        "segment": "Mid-tier", "tier": "Gold", "contact_pref": ["Email", "SMS"],
        "host": "Rita Bloom",
        "trips": [
            {"date": "2021-10-15", "nights": 2, "room": "Deluxe Queen", "gaming_win_loss": -1200, "food_spend": 280, "show_spend": 200, "spa_spend": 150, "offers_redeemed": ["Room $79/N", "Show x1"]},
            {"date": "2022-04-02", "nights": 2, "room": "Deluxe Queen", "gaming_win_loss": -1600, "food_spend": 320, "show_spend": 250, "spa_spend": 100, "offers_redeemed": ["Room $79/N", "F&B $100"]},
            {"date": "2022-10-29", "nights": 3, "room": "Deluxe King",  "gaming_win_loss": -2100, "food_spend": 380, "show_spend": 300, "spa_spend": 200, "offers_redeemed": ["Room Comp 1N", "Show x1", "Spa $75"]},
            {"date": "2023-05-12", "nights": 2, "room": "Deluxe Queen", "gaming_win_loss": -1400, "food_spend": 290, "show_spend": 200, "spa_spend": 120, "offers_redeemed": ["Room $79/N"]},
            {"date": "2023-12-02", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -1900, "food_spend": 350, "show_spend": 280, "spa_spend": 180, "offers_redeemed": ["Room $89/N", "F&B $100", "Show x1"]},
            {"date": "2024-05-18", "nights": 2, "room": "Deluxe Queen", "gaming_win_loss": -1700, "food_spend": 310, "show_spend": 220, "spa_spend": 130, "offers_redeemed": ["Room $79/N", "Show x1"]},
            {"date": "2024-12-06", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -2000, "food_spend": 360, "show_spend": 280, "spa_spend": 160, "offers_redeemed": ["Room $89/N", "F&B $100"]},
            {"date": "2025-06-21", "nights": 2, "room": "Deluxe Queen", "gaming_win_loss": -1800, "food_spend": 330, "show_spend": 240, "spa_spend": 140, "offers_redeemed": ["Room Comp 1N", "Show x1"]},
        ],
        "last_visit": "2026-05-15",
        "ytd_trips_2026": [
            {"date": "2026-05-15", "gaming_win_loss": -1900, "food_spend": 340, "show_spend": 250, "spa_spend": 140, "comp_cost": 520},
        ],
        "ytd_trips_2025": [
            {"date": "2025-06-21", "gaming_win_loss": -1800, "food_spend": 330, "show_spend": 240, "spa_spend": 140, "comp_cost": 480},
            {"date": "2025-12-14", "gaming_win_loss": -2100, "food_spend": 370, "show_spend": 280, "spa_spend": 150, "comp_cost": 540},
        ],
        "avg_visits_per_year": 1.8, "avg_trip_gaming_loss": 1650, "avg_trip_total_spend": 2360,
        "notes": "Very consistent, responds to all channels. Loves shows and light spa. Slots only. Small offers still drive trips.",
        "reinvestment_cap_pct": 0.20,
    },
    {
        "id": "G012", "name": "Tom Gilroy", "age": 49, "city": "Portland, OR",
        "segment": "Mid-tier", "tier": "Gold", "contact_pref": ["Phone", "Email"],
        "host": "Rita Bloom",
        "trips": [
            {"date": "2021-09-05", "nights": 2, "room": "Standard King", "gaming_win_loss": -900, "food_spend": 200, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Room $69/N"]},
            {"date": "2022-06-18", "nights": 2, "room": "Deluxe Queen",  "gaming_win_loss": -1300,"food_spend": 240, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Room $79/N", "F&B $75"]},
            {"date": "2023-01-28", "nights": 2, "room": "Deluxe Queen",  "gaming_win_loss": -1100,"food_spend": 220, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Room $79/N"]},
            {"date": "2023-08-14", "nights": 2, "room": "Standard King", "gaming_win_loss": -800, "food_spend": 180, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Room $69/N", "F&B $50"]},
            {"date": "2024-02-09", "nights": 2, "room": "Deluxe Queen",  "gaming_win_loss": -1400,"food_spend": 260, "show_spend": 0, "spa_spend": 0, "offers_redeemed": ["Room $79/N"]},
        ],
        "last_visit": "2025-08-20",
        "ytd_trips_2026": [],
        "ytd_trips_2025": [
            {"date": "2025-08-20", "gaming_win_loss": -1200, "food_spend": 230, "show_spend": 0, "spa_spend": 0, "comp_cost": 300},
        ],
        "avg_visits_per_year": 1.2, "avg_trip_gaming_loss": 1100, "avg_trip_total_spend": 1500,
        "notes": "Budget-conscious, rarely uses F&B comps fully. Pure slots, never shows. Responds to low room rate + small F&B. LAPSED — 10 months.",
        "reinvestment_cap_pct": 0.18,
    },
    {
        "id": "G013", "name": "Mei Lin", "age": 33, "city": "Las Vegas, NV",
        "segment": "Developing", "tier": "Silver", "contact_pref": ["SMS", "Email"],
        "host": "Rita Bloom",
        "trips": [
            {"date": "2022-11-19", "nights": 1, "room": "Standard Queen", "gaming_win_loss": -600, "food_spend": 120, "show_spend": 150, "spa_spend": 0, "offers_redeemed": ["Room $59/N"]},
            {"date": "2023-04-07", "nights": 2, "room": "Standard King",  "gaming_win_loss": -850, "food_spend": 180, "show_spend": 200, "spa_spend": 0, "offers_redeemed": ["Room $69/N", "Show x1"]},
            {"date": "2023-10-22", "nights": 2, "room": "Deluxe Queen",   "gaming_win_loss": -1100,"food_spend": 220, "show_spend": 250, "spa_spend": 0, "offers_redeemed": ["Room $79/N", "Show x1"]},
            {"date": "2024-03-15", "nights": 2, "room": "Deluxe Queen",   "gaming_win_loss": -1300,"food_spend": 250, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Show x1"]},
            {"date": "2024-10-08", "nights": 2, "room": "Deluxe Queen",   "gaming_win_loss": -1500,"food_spend": 270, "show_spend": 320, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Show x1"]},
            {"date": "2025-04-19", "nights": 2, "room": "Luxury King",    "gaming_win_loss": -1800,"food_spend": 300, "show_spend": 350, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Show x1", "F&B $100"]},
        ],
        "last_visit": "2026-06-01",
        "ytd_trips_2026": [
            {"date": "2026-06-01", "gaming_win_loss": -1600, "food_spend": 280, "show_spend": 340, "spa_spend": 0, "comp_cost": 450},
        ],
        "ytd_trips_2025": [
            {"date": "2025-04-19", "gaming_win_loss": -1800, "food_spend": 300, "show_spend": 350, "spa_spend": 0, "comp_cost": 500},
            {"date": "2025-11-07", "gaming_win_loss": -1700, "food_spend": 290, "show_spend": 330, "spa_spend": 0, "comp_cost": 480},
        ],
        "avg_visits_per_year": 1.6, "avg_trip_gaming_loss": 963, "avg_trip_total_spend": 1633,
        "notes": "Local — drives herself, no flight needed. Growing trend. Show offers always convert. Gaming increasing each trip — potential for upgrade.",
        "reinvestment_cap_pct": 0.22,
    },
    {
        "id": "G014", "name": "Jerome Washington", "age": 42, "city": "Henderson, NV",
        "segment": "Mid-tier", "tier": "Gold", "contact_pref": ["SMS", "Phone"],
        "host": "Rita Bloom",
        "trips": [
            {"date": "2022-07-22", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -1800, "food_spend": 350, "show_spend": 250, "spa_spend": 0, "offers_redeemed": ["Room $89/N", "F&B $100"]},
            {"date": "2023-02-10", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -2200, "food_spend": 380, "show_spend": 280, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Gaming $250"]},
            {"date": "2023-09-29", "nights": 3, "room": "Luxury King",  "gaming_win_loss": -3100, "food_spend": 450, "show_spend": 350, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "F&B $150", "Gaming $250"]},
            {"date": "2024-04-18", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -2500, "food_spend": 400, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Gaming $250"]},
            {"date": "2024-11-22", "nights": 3, "room": "Luxury King",  "gaming_win_loss": -3400, "food_spend": 480, "show_spend": 380, "spa_spend": 0, "offers_redeemed": ["Room Comp 2N", "F&B $150", "Show x1"]},
            {"date": "2025-05-30", "nights": 2, "room": "Deluxe King",  "gaming_win_loss": -2800, "food_spend": 420, "show_spend": 300, "spa_spend": 0, "offers_redeemed": ["Room Comp 1N", "Gaming $250"]},
        ],
        "last_visit": "2026-04-10",
        "ytd_trips_2026": [
            {"date": "2026-04-10", "gaming_win_loss": -2900, "food_spend": 440, "show_spend": 320, "spa_spend": 0, "comp_cost": 780},
        ],
        "ytd_trips_2025": [
            {"date": "2025-05-30", "gaming_win_loss": -2800, "food_spend": 420, "show_spend": 300, "spa_spend": 0, "comp_cost": 720},
            {"date": "2025-12-12", "gaming_win_loss": -3100, "food_spend": 460, "show_spend": 350, "spa_spend": 0, "comp_cost": 800},
        ],
        "avg_visits_per_year": 1.8, "avg_trip_gaming_loss": 2633, "avg_trip_total_spend": 3483,
        "notes": "Local, comes monthly. Blackjack and slots mix. SMS works best. Gaming comp plus room always converts.",
        "reinvestment_cap_pct": 0.21,
    },
]


OFFER_CATALOG = {
    "rooms": {
        "Standard Queen":  {"rack_rate": 179,  "comp_cost": 89,   "eligible_segments": ["Developing", "Mid-tier"]},
        "Standard King":   {"rack_rate": 199,  "comp_cost": 99,   "eligible_segments": ["Developing", "Mid-tier"]},
        "Deluxe Queen":    {"rack_rate": 249,  "comp_cost": 124,  "eligible_segments": ["Developing", "Mid-tier", "Premium"]},
        "Deluxe King":     {"rack_rate": 289,  "comp_cost": 144,  "eligible_segments": ["Mid-tier", "Premium"]},
        "Luxury King":     {"rack_rate": 389,  "comp_cost": 195,  "eligible_segments": ["Premium", "High Roller"]},
        "Kaggle King":    {"rack_rate": 449,  "comp_cost": 225,  "eligible_segments": ["Premium", "High Roller"]},
        "Kaggle Queen":   {"rack_rate": 429,  "comp_cost": 215,  "eligible_segments": ["Premium", "High Roller"]},
        "Kaggle Suite":   {"rack_rate": 699,  "comp_cost": 350,  "eligible_segments": ["High Roller", "Whale"]},
        "Grand Suite":   {"rack_rate": 999,  "comp_cost": 500,  "eligible_segments": ["High Roller", "Whale"]},
        "Signature Villa":     {"rack_rate": 2499, "comp_cost": 1250, "eligible_segments": ["Whale"]},
        "Penthouse Villa":       {"rack_rate": 4999, "comp_cost": 2500, "eligible_segments": ["Whale"]},
    },
    "food_comps": {
        "F&B $50":   {"cost": 50,   "eligible_segments": ["Developing", "Mid-tier"]},
        "F&B $100":  {"cost": 100,  "eligible_segments": ["Developing", "Mid-tier"]},
        "F&B $200":  {"cost": 200,  "eligible_segments": ["Mid-tier", "Premium"]},
        "F&B $300":  {"cost": 300,  "eligible_segments": ["Premium"]},
        "F&B $500":  {"cost": 500,  "eligible_segments": ["Premium", "High Roller"]},
        "F&B $800":  {"cost": 800,  "eligible_segments": ["High Roller"]},
        "F&B $1200": {"cost": 1200, "eligible_segments": ["High Roller", "Whale"]},
        "F&B $2000": {"cost": 2000, "eligible_segments": ["Whale"]},
    },
    "gaming_comps": {
        "Gaming $250":  {"cost": 250,  "eligible_segments": ["Mid-tier", "Premium"]},
        "Gaming $500":  {"cost": 500,  "eligible_segments": ["Premium"]},
        "Gaming $1000": {"cost": 1000, "eligible_segments": ["Premium", "High Roller"]},
        "Gaming $1500": {"cost": 1500, "eligible_segments": ["High Roller"]},
        "Gaming $2000": {"cost": 2000, "eligible_segments": ["High Roller"]},
        "Gaming $3000": {"cost": 3000, "eligible_segments": ["High Roller", "Whale"]},
        "Gaming $5000": {"cost": 5000, "eligible_segments": ["Whale"]},
        "Gaming $8000": {"cost": 8000, "eligible_segments": ["Whale"]},
    },
    "shows": {
        "Show x1":  {"cost": 150,  "eligible_segments": ["Developing", "Mid-tier", "Premium", "High Roller"]},
        "Show x2":  {"cost": 300,  "eligible_segments": ["Mid-tier", "Premium", "High Roller"]},
        "Show VIP": {"cost": 600,  "eligible_segments": ["High Roller", "Whale"]},
    },
    "spa": {
        "Spa $75":     {"cost": 75,  "eligible_segments": ["Developing", "Mid-tier"]},
        "Spa $150":    {"cost": 150, "eligible_segments": ["Mid-tier", "Premium"]},
        "Spa $250":    {"cost": 250, "eligible_segments": ["Premium", "High Roller"]},
        "Spa $500":    {"cost": 500, "eligible_segments": ["High Roller"]},
        "Spa Package": {"cost": 900, "eligible_segments": ["High Roller", "Whale"]},
    },
}

GUARDRAILS = {
    "reinvestment_hard_cap_pct": 0.40,
    "min_trips_for_room_comp": 2,
    "min_trips_for_gaming_comp": 3,
    "re_offer_cooldown_days": 45,
    "max_total_offer_cost": {
        "Developing": 400,
        "Mid-tier": 900,
        "Premium": 3500,
        "High Roller": 12000,
        "Whale": 60000,
    },
    "contact_time_rules": {
        "Phone":           "Business hours 9am–7pm guest local time, weekdays",
        "Email":           "Any time — send Tuesday/Wednesday for best open rates",
        "SMS":             "Weekend morning 9–11am for best response",
        "Personal Letter": "Allow 3 business days delivery lead time",
    },
}


# ── Past offer history ────────────────────────────────────────────────────────
# Keyed by guest ID. Each entry: offer made, outcome (Accepted/Declined), reason.
# This is SOURCE DATA — read-only. Never modify at runtime.

OFFER_HISTORY = {
    "G001": [  # Richard Harmon — Whale
        {"date": "2025-10-01", "offer": {"room": "Penthouse Villa x3N", "food": "F&B $2000", "gaming": "Gaming $8000", "show": "Show VIP", "spa": "Spa Package", "total": 20900}, "outcome": "Accepted", "channel": "Phone", "notes": "Responded immediately. Said gaming comp was the deciding factor."},
        {"date": "2025-03-15", "offer": {"room": "Signature Villa x2N", "food": "F&B $1500", "gaming": "Gaming $5000", "show": None, "spa": "Spa Package", "total": 14750}, "outcome": "Accepted", "channel": "Phone", "notes": "Booked within 2 hours of call. Wife happy with spa."},
        {"date": "2024-09-01", "offer": {"room": "Signature Villa x3N", "food": "F&B $2000", "gaming": "Gaming $6000", "show": "Show VIP", "spa": None, "total": 17750}, "outcome": "Accepted", "channel": "Phone", "notes": "Always answers phone call from Maria. No hesitation."},
        {"date": "2024-01-20", "offer": {"room": "Penthouse Villa x2N", "food": "F&B $2000", "gaming": "Gaming $3000", "show": None, "spa": None, "total": 10000}, "outcome": "Declined", "channel": "Phone", "notes": "Said gaming comp was too low. Booked a competitor instead. Need minimum $5000 gaming."},
    ],
    "G002": [  # Linda Zhao — Whale
        {"date": "2025-11-20", "offer": {"room": "Grand Suite x3N", "food": "F&B $2000", "gaming": "Gaming $3500", "show": "Show VIP", "spa": "Spa Package", "total": 16400}, "outcome": "Accepted", "channel": "Email", "notes": "Spa package was key. Booked Summit Spa immediately."},
        {"date": "2025-04-10", "offer": {"room": "Signature Villa x2N", "food": "F&B $1500", "gaming": "Gaming $3000", "show": "Show x2", "spa": "Spa Package", "total": 13300}, "outcome": "Accepted", "channel": "Phone", "notes": "Happy with offer. Brought a friend — extra room request next time."},
        {"date": "2024-10-05", "offer": {"room": "Kaggle Suite x2N", "food": "F&B $1200", "gaming": "Gaming $2000", "show": None, "spa": "Spa $500", "total": 7200}, "outcome": "Declined", "channel": "Email", "notes": "Said room was not nice enough. Expects Signature Villa or Grand Suite minimum. Never downgrade her room."},
        {"date": "2024-03-18", "offer": {"room": "Grand Suite x3N", "food": "F&B $2000", "gaming": "Gaming $3500", "show": "Show x2", "spa": "Spa Package", "total": 16200}, "outcome": "Accepted", "channel": "Phone", "notes": "Perfect offer. Stayed extra night on her own."},
    ],
    "G003": [  # Victor Castellano — High Roller
        {"date": "2026-01-02", "offer": {"room": "Kaggle Suite x3N", "food": "F&B $1200", "gaming": "Gaming $3000", "show": None, "spa": None, "total": 6300}, "outcome": "Accepted", "channel": "Phone", "notes": "Picked up on first ring. Gaming comp always converts him."},
        {"date": "2025-08-20", "offer": {"room": "Grand Suite x3N", "food": "F&B $1200", "gaming": "Gaming $2000", "show": None, "spa": None, "total": 6700}, "outcome": "Accepted", "channel": "Phone", "notes": "No issues. Stayed 4 nights on own dime."},
        {"date": "2024-12-10", "offer": {"room": "Kaggle Suite x2N", "food": "F&B $800", "gaming": "Gaming $1500", "show": None, "spa": None, "total": 3500}, "outcome": "Declined", "channel": "Email", "notes": "Never responds to email. Needs phone. Also gaming comp too low."},
        {"date": "2024-06-15", "offer": {"room": "Grand Suite x2N", "food": "F&B $1200", "gaming": "Gaming $2000", "show": None, "spa": None, "total": 5200}, "outcome": "Accepted", "channel": "Phone", "notes": "Solid offer. Pure gaming focus works every time."},
    ],
    "G004": [  # Natasha Brennan — Premium
        {"date": "2026-04-10", "offer": {"room": "Kaggle King x2N", "food": "F&B $300", "gaming": "Gaming $800", "show": "Show x2", "spa": "Spa $250", "total": 2000}, "outcome": "Accepted", "channel": "Email", "notes": "Detailed breakdown in email sealed it. Loved the show + spa combo."},
        {"date": "2025-10-22", "offer": {"room": "Luxury King x3N", "food": "F&B $300", "gaming": "Gaming $1000", "show": "Show x2", "spa": None, "total": 2185}, "outcome": "Accepted", "channel": "Email", "notes": "Fast response. Said gaming comp + shows is ideal for her."},
        {"date": "2025-03-05", "offer": {"room": "Luxury King x2N", "food": "F&B $200", "gaming": None, "show": "Show x1", "spa": "Spa $250", "total": 1040}, "outcome": "Declined", "channel": "Email", "notes": "Too small. No gaming comp was the dealbreaker. She expects at least $500 gaming."},
        {"date": "2024-08-12", "offer": {"room": "Kaggle King x2N", "food": "F&B $300", "gaming": "Gaming $800", "show": "Show x2", "spa": "Spa $250", "total": 2000}, "outcome": "Accepted", "channel": "Email", "notes": "Identical to her last accepted offer. Formula works."},
    ],
    "G005": [  # Marcus Webb — High Roller
        {"date": "2026-04-28", "offer": {"room": "Kaggle King x3N", "food": "F&B $500", "gaming": "Gaming $1500", "show": None, "spa": None, "total": 4175}, "outcome": "Accepted", "channel": "Email", "notes": "Always email. Gaming comp the key driver."},
        {"date": "2025-10-30", "offer": {"room": "Luxury King x2N", "food": "F&B $500", "gaming": "Gaming $1000", "show": None, "spa": None, "total": 2890}, "outcome": "Accepted", "channel": "Email", "notes": "No hesitation. Blackjack table was calling him."},
        {"date": "2025-04-15", "offer": {"room": "Kaggle King x2N", "food": "F&B $500", "gaming": "Gaming $1500", "show": "Show x1", "spa": None, "total": 3590}, "outcome": "Declined", "channel": "Phone", "notes": "Did not answer phone. Emailed instead — too late, he had already booked elsewhere. Strict email-only."},
        {"date": "2024-09-20", "offer": {"room": "Luxury King x3N", "food": "F&B $500", "gaming": "Gaming $1500", "show": None, "spa": None, "total": 3085}, "outcome": "Accepted", "channel": "Email", "notes": "Email with clear gaming match play details works every time."},
    ],
    "G006": [  # Priya Nair — High Roller
        {"date": "2026-01-25", "offer": {"room": "Luxury King x3N", "food": "F&B $500", "gaming": "Gaming $1200", "show": "Show x2", "spa": "Spa $250", "total": 3535}, "outcome": "Accepted", "channel": "Email", "notes": "Brought 2 friends. Asked about extra room for group next time."},
        {"date": "2025-08-30", "offer": {"room": "Kaggle Queen x2N", "food": "F&B $500", "gaming": "Gaming $1000", "show": "Show x2", "spa": "Spa $250", "total": 2780}, "outcome": "Accepted", "channel": "Email", "notes": "Show tickets are a must for her group trips."},
        {"date": "2025-01-10", "offer": {"room": "Luxury King x2N", "food": "F&B $500", "gaming": "Gaming $1200", "show": None, "spa": None, "total": 2090}, "outcome": "Declined", "channel": "Email", "notes": "No shows = no deal. She travels for the experience, not just gaming."},
        {"date": "2024-06-08", "offer": {"room": "Luxury King x3N", "food": "F&B $500", "gaming": "Gaming $1000", "show": "Show x2", "spa": "Spa $250", "total": 3035}, "outcome": "Accepted", "channel": "Email", "notes": "Show x2 + spa confirmed. Always accepts when experience package is complete."},
    ],
    "G007": [  # Derek Fontaine — High Roller (lapsed)
        {"date": "2025-05-22", "offer": {"room": "Grand Suite x3N", "food": "F&B $1200", "gaming": "Gaming $3000", "show": None, "spa": None, "total": 6900}, "outcome": "Accepted", "channel": "Phone", "notes": "Took 3 days to call back. High gaming comp was the hook."},
        {"date": "2024-12-01", "offer": {"room": "Kaggle Suite x2N", "food": "F&B $800", "gaming": "Gaming $2000", "show": None, "spa": None, "total": 4500}, "outcome": "Accepted", "channel": "Phone", "notes": "Came for Christmas. Stayed through New Year on own."},
        {"date": "2024-05-10", "offer": {"room": "Grand Suite x2N", "food": "F&B $1200", "gaming": "Gaming $1500", "show": None, "spa": None, "total": 5200}, "outcome": "Declined", "channel": "Phone", "notes": "Said gaming comp not worth the flight. Needs $2000+ gaming to make trip worthwhile."},
        {"date": "2023-10-15", "offer": {"room": "Kaggle Suite x3N", "food": "F&B $1200", "gaming": "Gaming $2000", "show": None, "spa": None, "total": 5250}, "outcome": "Accepted", "channel": "Phone", "notes": "Pure gaming guest. Never spa or shows. Suite + big gaming comp = trip confirmed."},
    ],
    "G008": [  # Carlos Reyes — Premium
        {"date": "2026-03-10", "offer": {"room": "Luxury King x2N", "food": "F&B $300", "gaming": "Gaming $600", "show": "Show x1", "spa": None, "total": 1740}, "outcome": "Accepted", "channel": "Phone", "notes": "Phone call closed it fast. Gaming comp important to him."},
        {"date": "2025-12-05", "offer": {"room": "Kaggle King x2N", "food": "F&B $300", "gaming": "Gaming $800", "show": "Show x1", "spa": None, "total": 1895}, "outcome": "Accepted", "channel": "Email", "notes": "Email + follow-up phone worked. Responded to show + gaming combo."},
        {"date": "2025-07-20", "offer": {"room": "Deluxe King x2N", "food": "F&B $200", "gaming": None, "show": None, "spa": None, "total": 488}, "outcome": "Declined", "channel": "Email", "notes": "Too small. No gaming comp. Will not come for just a room discount."},
        {"date": "2025-01-08", "offer": {"room": "Luxury King x2N", "food": "F&B $300", "gaming": "Gaming $600", "show": None, "spa": None, "total": 1590}, "outcome": "Accepted", "channel": "Phone", "notes": "Phone first, then sent email recap. Gaming comp sealed it."},
    ],
    "G009": [  # Angela Torres — Premium
        {"date": "2026-05-15", "offer": {"room": "Kaggle King x2N", "food": "F&B $300", "gaming": "Gaming $400", "show": "Show x1", "spa": None, "total": 1595}, "outcome": "Accepted", "channel": "Email", "notes": "Quick accept via email. Show offer always gets a yes."},
        {"date": "2025-11-28", "offer": {"room": "Luxury King x2N", "food": "F&B $300", "gaming": "Gaming $400", "show": "Show x1", "spa": None, "total": 1240}, "outcome": "Accepted", "channel": "SMS", "notes": "SMS notification worked — responded within 30 min."},
        {"date": "2025-05-10", "offer": {"room": "Deluxe King x2N", "food": "F&B $200", "gaming": None, "show": None, "spa": None, "total": 488}, "outcome": "Declined", "channel": "Email", "notes": "No show, no gaming = not interested. Show ticket is a must for her."},
        {"date": "2024-10-18", "offer": {"room": "Kaggle King x3N", "food": "F&B $300", "gaming": "Gaming $400", "show": "Show x1", "spa": None, "total": 1745}, "outcome": "Accepted", "channel": "Email", "notes": "3-night stay. Appreciates detailed email breakdown of offer value."},
    ],
    "G010": [  # Kevin Park — Premium
        {"date": "2026-04-05", "offer": {"room": "Kaggle King x3N", "food": "F&B $300", "gaming": "Gaming $600", "show": "Show x1", "spa": None, "total": 2025}, "outcome": "Accepted", "channel": "Email", "notes": "Spreadsheet-style email with itemized offer value worked perfectly."},
        {"date": "2025-08-22", "offer": {"room": "Luxury King x2N", "food": "F&B $300", "gaming": "Gaming $500", "show": "Show x1", "spa": None, "total": 1640}, "outcome": "Accepted", "channel": "Email", "notes": "Email only — never answers phone. Clear ROI framing in email."},
        {"date": "2025-02-14", "offer": {"room": "Kaggle King x2N", "food": "F&B $200", "gaming": None, "show": None, "spa": None, "total": 650}, "outcome": "Declined", "channel": "Phone", "notes": "Did not answer phone. Also no gaming comp = not worth trip from Seattle."},
        {"date": "2024-05-30", "offer": {"room": "Luxury King x2N", "food": "F&B $300", "gaming": "Gaming $500", "show": "Show x1", "spa": None, "total": 1490}, "outcome": "Accepted", "channel": "Email", "notes": "Email with total comp value prominently displayed. Gaming + show is his formula."},
    ],
    "G011": [  # Sandra Mitchell — Mid-tier
        {"date": "2026-05-02", "offer": {"room": "Deluxe Queen x2N", "food": "F&B $100", "gaming": None, "show": "Show x1", "spa": "Spa $75", "total": 523}, "outcome": "Accepted", "channel": "Email", "notes": "Show + spa combo gets her every time. Responds to email quickly."},
        {"date": "2025-12-01", "offer": {"room": "Deluxe King x2N", "food": "F&B $100", "gaming": None, "show": "Show x1", "spa": "Spa $75", "total": 563}, "outcome": "Accepted", "channel": "SMS", "notes": "SMS reminder after email worked. Holiday timing helped."},
        {"date": "2025-05-20", "offer": {"room": "Deluxe Queen x2N", "food": "F&B $100", "gaming": None, "show": None, "spa": None, "total": 348}, "outcome": "Declined", "channel": "Email", "notes": "No show or spa = no interest. She needs the full experience, not just room."},
        {"date": "2024-11-10", "offer": {"room": "Deluxe King x2N", "food": "F&B $100", "gaming": None, "show": "Show x1", "spa": "Spa $75", "total": 563}, "outcome": "Accepted", "channel": "Email", "notes": "Consistent offer, consistent result. Show + spa drives her decision every time."},
    ],
    "G012": [  # Tom Gilroy — Mid-tier (lapsed)
        {"date": "2025-07-15", "offer": {"room": "Deluxe Queen x2N", "food": "F&B $75", "gaming": None, "show": None, "spa": None, "total": 323}, "outcome": "Accepted", "channel": "Phone", "notes": "Phone call worked. Budget-focused — low room rate + small F&B is enough."},
        {"date": "2024-11-20", "offer": {"room": "Standard King x2N", "food": "F&B $50", "gaming": None, "show": None, "spa": None, "total": 248}, "outcome": "Declined", "channel": "Email", "notes": "Did not respond to email. Needs phone. Also too small even for him."},
        {"date": "2024-06-01", "offer": {"room": "Deluxe Queen x2N", "food": "F&B $75", "gaming": None, "show": None, "spa": None, "total": 323}, "outcome": "Accepted", "channel": "Phone", "notes": "Phone is the only channel that works. Keep offer simple."},
    ],
    "G013": [  # Mei Lin — Developing
        {"date": "2026-05-20", "offer": {"room": "Deluxe Queen x2N", "food": "F&B $100", "gaming": None, "show": "Show x1", "spa": None, "total": 398}, "outcome": "Accepted", "channel": "SMS", "notes": "SMS with show ticket offer = instant yes. Local guest, minimal planning needed."},
        {"date": "2025-10-25", "offer": {"room": "Standard King x2N", "food": "F&B $50", "gaming": None, "show": "Show x1", "spa": None, "total": 348}, "outcome": "Accepted", "channel": "SMS", "notes": "Show offer always works. Gaming is growing each trip."},
        {"date": "2025-03-08", "offer": {"room": "Standard Queen x1N", "food": None, "gaming": None, "show": None, "spa": None, "total": 89}, "outcome": "Declined", "channel": "Email", "notes": "No show = no interest. Also prefers SMS not email. Show is non-negotiable."},
        {"date": "2024-09-14", "offer": {"room": "Deluxe Queen x2N", "food": "F&B $50", "gaming": None, "show": "Show x1", "spa": None, "total": 348}, "outcome": "Accepted", "channel": "SMS", "notes": "SMS with show works every time for Mei Lin."},
    ],
    "G014": [  # Jerome Washington — Mid-tier
        {"date": "2026-03-28", "offer": {"room": "Luxury King x2N", "food": "F&B $150", "gaming": "Gaming $250", "show": "Show x1", "spa": None, "total": 740}, "outcome": "Accepted", "channel": "SMS", "notes": "SMS then phone follow-up closed it. Gaming comp + show works for him."},
        {"date": "2025-11-30", "offer": {"room": "Deluxe King x2N", "food": "F&B $150", "gaming": "Gaming $250", "show": None, "spa": None, "total": 638}, "outcome": "Accepted", "channel": "Phone", "notes": "Quick close on phone. Comes almost every month — easy sale."},
        {"date": "2025-09-10", "offer": {"room": "Deluxe King x2N", "food": "F&B $100", "gaming": None, "show": None, "spa": None, "total": 388}, "outcome": "Declined", "channel": "Email", "notes": "No gaming comp = no deal. Doesn't respond to email well either. Gaming comp is essential."},
        {"date": "2025-05-14", "offer": {"room": "Luxury King x2N", "food": "F&B $150", "gaming": "Gaming $250", "show": "Show x1", "spa": None, "total": 740}, "outcome": "Accepted", "channel": "SMS", "notes": "Same formula works. Local guest, comes regularly."},
    ],
}
