import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from . import analysis as an

DATA = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
app = FastAPI(title="Wind Forecast Portal API")


@lru_cache
def load():
    act = pd.read_csv(DATA / "actuals.csv", parse_dates=["start_time"])
    fc = pd.read_csv(DATA / "forecasts.csv", parse_dates=["start_time", "publish_time"])
    for d, cols in ((act, ["start_time"]), (fc, ["start_time", "publish_time"])):
        for c in cols:
            d[c] = pd.to_datetime(d[c], utc=True)
    return act, fc


def _valid_cutoff(c: str) -> str:
    try:
        h, m = c.split(":"); assert 0 <= int(h) < 24 and 0 <= int(m) < 60
    except Exception:
        raise HTTPException(422, "cutoff must be HH:MM")
    return c


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/forecast")
def forecast(day: str = Query(..., description="Delivery day YYYY-MM-DD (Jan 2026)"),
             cutoff: str = "09:00"):
    """Decision-time forecast for one delivery day, with actuals where already known."""
    _valid_cutoff(cutoff)
    act, fc = load()
    dec = an.decision_forecasts(fc, cutoff)
    local = dec.start_time.dt.tz_convert(an.TZ).dt.date.astype(str)
    dec = dec[local == day]
    if dec.empty:
        raise HTTPException(404, "no forecast available for that day")
    m = dec.merge(act, on="start_time", how="left")
    m["error_mw"] = m.forecast_mw - m.actual_mw
    pub = m.publish_time.max()
    return {
        "day": day, "cutoff": cutoff, "latest_publish_time": pub.isoformat(),
        "points": [{"t": r.start_time.isoformat(), "forecast_mw": r.forecast_mw,
                    "actual_mw": None if pd.isna(r.actual_mw) else r.actual_mw,
                    "publish_time": r.publish_time.isoformat(), "horizon_h": round(r.horizon_h, 1)}
                   for r in m.itertuples()],
    }


@app.get("/api/accuracy")
def accuracy(cutoff: str = "09:00", day: str | None = None):
    """Error metrics for decision-time forecasts (whole month, or a single day)."""
    _valid_cutoff(cutoff)
    act, fc = load()
    m = an.join_actuals(an.decision_forecasts(fc, cutoff), act)
    if day:
        m = m[m.start_time.dt.tz_convert(an.TZ).dt.date.astype(str) == day]
    return {"cutoff": cutoff, "summary": an.metrics(m), "by_hour": an.by_hour(m) if len(m) else [],
            "by_day": an.by_day(m) if len(m) else [],
            "by_horizon": an.by_horizon(fc, act)}


@app.get("/api/errors")
def errors(cutoff: str = "09:00", bins: int = 30):
    """Raw signed errors histogram for the distribution chart."""
    _valid_cutoff(cutoff)
    import numpy as np
    act, fc = load()
    m = an.join_actuals(an.decision_forecasts(fc, cutoff), act)
    if m.empty:
        return {"bins": []}
    counts, edges = np.histogram(m.error_mw, bins=bins)
    return {"bins": [{"from": float(edges[i]), "to": float(edges[i + 1]), "count": int(c)} for i, c in enumerate(counts)]}


# Serve built React app when present (single-container deployment)
STATIC = Path(os.getenv("STATIC_DIR", "/app/static"))
if STATIC.exists():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
