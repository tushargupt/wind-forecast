"""Core business logic: which forecast was available at decision time, and how accurate was it."""
import numpy as np
import pandas as pd

TZ = "Europe/London"


def decision_forecasts(fc: pd.DataFrame, cutoff: str = "09:00") -> pd.DataFrame:
    """For every target half-hour, keep the LATEST forecast published at or before
    the day-ahead cutoff: (delivery day - 1) at `cutoff` UK local time.

    Returns columns: start_time, publish_time, forecast_mw, horizon_h
    """
    if fc.empty:
        return fc.assign(horizon_h=pd.Series(dtype=float))
    hh, mm = (int(x) for x in cutoff.split(":"))
    df = fc.copy()
    local_day = df["start_time"].dt.tz_convert(TZ).dt.normalize()  # delivery day, local midnight
    cut = (local_day - pd.Timedelta(days=1)).dt.tz_localize(None) + pd.Timedelta(hours=hh, minutes=mm)
    df["cutoff_time"] = cut.dt.tz_localize(TZ, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    df = df[df["publish_time"] <= df["cutoff_time"]]
    df = df.sort_values("publish_time").groupby("start_time", as_index=False).tail(1)
    df["horizon_h"] = (df["start_time"] - df["publish_time"]).dt.total_seconds() / 3600
    return df.drop(columns="cutoff_time").sort_values("start_time").reset_index(drop=True)


def join_actuals(dec: pd.DataFrame, act: pd.DataFrame) -> pd.DataFrame:
    """Attach each actual half-hour to the forecast covering it.
    WINDFOR is hourly while FUELHH is half-hourly, so an hourly forecast is applied to
    both half-hours of that hour (as-of join, max 31 min back). Works for half-hourly forecasts too."""
    if dec.empty or act.empty:
        return pd.DataFrame(columns=["start_time", "forecast_mw", "actual_mw", "error_mw", "abs_error_mw"])
    right = dec.sort_values("start_time")
    m = pd.merge_asof(act.sort_values("start_time"), right, on="start_time",
                      direction="backward", tolerance=pd.Timedelta("31min"))
    m = m.dropna(subset=["forecast_mw"]).reset_index(drop=True)
    m["error_mw"] = m["forecast_mw"] - m["actual_mw"]  # + = over-forecast (risk: bought too little)
    m["abs_error_mw"] = m["error_mw"].abs()
    return m


def _exact_join(fc: pd.DataFrame, act: pd.DataFrame) -> pd.DataFrame:
    m = fc.merge(act, on="start_time", how="inner")
    m["error_mw"] = m["forecast_mw"] - m["actual_mw"]
    m["abs_error_mw"] = m["error_mw"].abs()
    return m


def metrics(m: pd.DataFrame) -> dict:
    if m.empty:
        return {"n": 0}
    e, a = m["error_mw"], m["actual_mw"]
    nz = a > 100  # MAPE is meaningless near zero wind
    q = lambda s, p: float(np.quantile(s, p))
    return {
        "n": int(len(m)),
        "mae_mw": float(e.abs().mean()),
        "rmse_mw": float(np.sqrt((e ** 2).mean())),
        "bias_mw": float(e.mean()),
        "mape_pct": float((e[nz].abs() / a[nz]).mean() * 100) if nz.any() else None,
        "mean_actual_mw": float(a.mean()),
        "nmae_pct": float(e.abs().mean() / a.mean() * 100),
        "abs_error_p50_mw": q(e.abs(), .5),
        "abs_error_p90_mw": q(e.abs(), .9),
        "abs_error_p95_mw": q(e.abs(), .95),
        # 90% band of signed error: use as "forecast - X ... forecast + Y"
        "error_p05_mw": q(e, .05),
        "error_p95_mw": q(e, .95),
        "error_std_mw": float(e.std()),
        "mae_after_bias_mw": float((e - e.mean()).abs().mean()),  # miss left once the steady lean is removed
        "over_forecast_share_pct": float((e > 0).mean() * 100),
    }


def by_hour(m: pd.DataFrame) -> list[dict]:
    g = m.assign(hour=m["start_time"].dt.tz_convert(TZ).dt.hour).groupby("hour")
    return [{"hour": int(h), "mae_mw": float(d.abs_error_mw.mean()), "bias_mw": float(d.error_mw.mean())} for h, d in g]


def by_day(m: pd.DataFrame) -> list[dict]:
    g = m.assign(day=m["start_time"].dt.tz_convert(TZ).dt.date.astype(str)).groupby("day")
    return [{"day": d, "mae_mw": float(x.abs_error_mw.mean()), "bias_mw": float(x.error_mw.mean()),
             "mean_actual_mw": float(x.actual_mw.mean())} for d, x in g]


def by_horizon(fc: pd.DataFrame, act: pd.DataFrame, bucket_h: int = 6) -> list[dict]:
    """Accuracy vs. forecast lead time using ALL published forecasts (not just decision-time)."""
    m = _exact_join(fc.assign(horizon_h=(fc.start_time - fc.publish_time).dt.total_seconds() / 3600), act)
    m = m[m.horizon_h >= 0]
    m["bucket"] = (m.horizon_h // bucket_h * bucket_h).astype(int)
    return [{"horizon_from_h": int(b), "horizon_to_h": int(b + bucket_h),
             "mae_mw": float(d.abs_error_mw.mean()), "n": int(len(d))} for b, d in m.groupby("bucket")]
