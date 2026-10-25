"""Thin client for the Elexon Insights (BMRS) open API. No API key required.

NOTE: parameter names below should be verified against the live docs
(https://bmrs.elexon.co.uk/api-documentation) - see README "Verification".
"""
from datetime import datetime, timedelta
import httpx
import pandas as pd

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
CHUNK_DAYS = 7  # stream endpoints limit the window size; chunk to be safe


def _chunks(start: datetime, end: datetime, days: int = CHUNK_DAYS):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def _get(client: httpx.Client, url: str, params: dict) -> list[dict]:
    r = client.get(url, params=params, timeout=60)
    r.raise_for_status()
    body = r.json()
    return body["data"] if isinstance(body, dict) and "data" in body else body


def fetch_actuals(start: datetime, end: datetime) -> pd.DataFrame:
    """FUELHH, WIND only -> columns: start_time (UTC), actual_mw."""
    rows = []
    with httpx.Client() as c:
        for a, b in _chunks(start, end):
            rows += _get(c, f"{BASE}/FUELHH/stream", {
                "settlementDateFrom": a.date().isoformat(),
                "settlementDateTo": b.date().isoformat(),
                "fuelType": "WIND",
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["start_time", "actual_mw"])
    df = df[df["fuelType"] == "WIND"]
    df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
    df = df.rename(columns={"generation": "actual_mw"})
    return (df[["start_time", "actual_mw"]]
            .drop_duplicates("start_time", keep="last")
            .sort_values("start_time").reset_index(drop=True))


def fetch_forecasts(publish_from: datetime, publish_to: datetime) -> pd.DataFrame:
    """WINDFOR -> columns: start_time, publish_time (UTC), forecast_mw."""
    rows = []
    with httpx.Client() as c:
        for a, b in _chunks(publish_from, publish_to):
            rows += _get(c, f"{BASE}/WINDFOR/stream", {
                "publishDateTimeFrom": a.strftime("%Y-%m-%dT%H:%MZ"),
                "publishDateTimeTo": b.strftime("%Y-%m-%dT%H:%MZ"),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["start_time", "publish_time", "forecast_mw"])
    df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
    df["publish_time"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df.rename(columns={"generation": "forecast_mw"})
    return (df[["start_time", "publish_time", "forecast_mw"]]
            .drop_duplicates(["start_time", "publish_time"], keep="last")
            .sort_values(["start_time", "publish_time"]).reset_index(drop=True))
