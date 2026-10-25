"""Run from repo root: python3 patch_alignment.py
1) align hourly forecasts to half-hourly actuals  2) split bias from random error  3) UI line for it."""
import re, pathlib

p = pathlib.Path("backend/app/analysis.py"); s = p.read_text()

old_join = s[s.index("def join_actuals"):s.index("def metrics")]
new_join = '''def join_actuals(dec: pd.DataFrame, act: pd.DataFrame) -> pd.DataFrame:
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


'''
s = s.replace(old_join, new_join)
s = s.replace("m = join_actuals(fc.assign(horizon_h=(fc.start_time - fc.publish_time).dt.total_seconds() / 3600), act)",
              "m = _exact_join(fc.assign(horizon_h=(fc.start_time - fc.publish_time).dt.total_seconds() / 3600), act)")
s = s.replace('        "over_forecast_share_pct"',
              '        "error_std_mw": float(e.std()),\n        "mae_after_bias_mw": float((e - e.mean()).abs().mean()),  # miss left once the steady lean is removed\n        "over_forecast_share_pct"')
p.write_text(s)

p = pathlib.Path("frontend/src/App.jsx"); s = p.read_text()
marker = '<div><dt>Percentage error</dt>'
extra = ('<div><dt>Steady lean vs random miss</dt><dd>{mw(s.mae_after_bias_mw)} MW<small>typical miss left after removing the lean of {mw(s.bias_mw)} MW. '
         'The lean is a consistent gap you can correct for; the rest is genuine uncertainty.</small></dd></div>\n            ')
if "Steady lean" not in s:
    s = s.replace(marker, extra + marker)
p.write_text(s)
print("patched")