import pandas as pd
from app import analysis as an


def _fc(rows):
    return pd.DataFrame(rows, columns=["start_time", "publish_time", "forecast_mw"]).astype(
        {"start_time": "datetime64[ns, UTC]", "publish_time": "datetime64[ns, UTC]"})


def test_picks_latest_forecast_before_cutoff():
    t = "2026-01-10 12:00:00+00:00"
    fc = _fc([(t, "2026-01-08 06:00:00+00:00", 1000),
              (t, "2026-01-09 08:00:00+00:00", 2000),   # latest before 09:00 cutoff on D-1
              (t, "2026-01-09 10:00:00+00:00", 3000)])  # published after cutoff -> must be ignored
    out = an.decision_forecasts(fc, "09:00")
    assert len(out) == 1 and out.forecast_mw.iloc[0] == 2000


def test_no_forecast_before_cutoff_is_dropped():
    fc = _fc([("2026-01-10 12:00:00+00:00", "2026-01-09 11:00:00+00:00", 500)])
    assert an.decision_forecasts(fc, "09:00").empty


def test_metrics_basic():
    m = pd.DataFrame({"start_time": pd.to_datetime(["2026-01-01", "2026-01-02"], utc=True),
                      "forecast_mw": [1200., 800.], "actual_mw": [1000., 1000.]})
    m["error_mw"] = m.forecast_mw - m.actual_mw
    m["abs_error_mw"] = m.error_mw.abs()
    r = an.metrics(m)
    assert r["mae_mw"] == 200 and r["bias_mw"] == 0 and r["rmse_mw"] == 200
