"""One-off: download January 2026 data and save snapshots into backend/data/.
Run:  python scripts_fetch.py
Forecasts are fetched from 14 Dec 2025 so decisions made on 31 Dec for 1 Jan are covered.
"""
from datetime import datetime
from app.elexon import fetch_actuals, fetch_forecasts

if __name__ == "__main__":
    a = fetch_actuals(datetime(2026, 1, 1), datetime(2026, 2, 1))
    f = fetch_forecasts(datetime(2025, 12, 14), datetime(2026, 2, 1))
    f = f[(f.start_time >= "2026-01-01") & (f.start_time < "2026-02-01")]
    a = a[(a.start_time >= "2026-01-01") & (a.start_time < "2026-02-01")]
    a.to_csv("data/actuals.csv", index=False)
    f.to_csv("data/forecasts.csv", index=False)
    print(f"actuals={len(a)} forecasts={len(f)}")
