import { useEffect, useState } from "react";
import { getForecast, getAccuracy, getErrors } from "./api.js";
import { DayChart, ErrorHistogram, HourChart, DayTrend, HorizonChart } from "./charts.jsx";
import { JAN_DAYS, prettyDay, mw, dayTime } from "./format.js";

const CUTOFFS = ["08:00", "09:00", "09:30", "10:00", "11:00"];

function useLoad(fn, deps) {
  const [s, set] = useState({ loading: true });
  useEffect(() => {
    let live = true;
    set({ loading: true });
    fn().then((data) => live && set({ data }), (error) => live && set({ error: error.message }));
    return () => { live = false; };
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
  return s;
}

export default function App() {
  const [day, setDay] = useState("2026-01-15");
  const [cutoff, setCutoff] = useState("09:00");
  const fc = useLoad(() => getForecast(day, cutoff), [day, cutoff]);
  const acc = useLoad(() => getAccuracy(cutoff), [cutoff]);
  const err = useLoad(() => getErrors(cutoff), [cutoff]);

  const s = acc.data?.summary;
  const pts = fc.data?.points;
  const avgForecast = pts ? pts.reduce((a, p) => a + p.forecast_mw, 0) / pts.length : null;
  const shortfall = s ? Math.max(0, s.error_p95_mw) : null;

  return (
    <main>
      <header>
        <h1>Wind cover desk</h1>
        <p className="sub">UK day-ahead buying: what the wind forecast says, and how far to trust it. January 2026, national wind, Elexon data.</p>
        <div className="controls">
          <label>Delivery day
            <select value={day} onChange={(e) => setDay(e.target.value)}>
              {JAN_DAYS.map((d) => <option key={d} value={d}>{prettyDay(d)}</option>)}
            </select>
          </label>
          <label>Forecast cut-off on the day before (UK time)
            <select value={cutoff} onChange={(e) => setCutoff(e.target.value)}>
              {CUTOFFS.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
        </div>
      </header>

      <section className="hero" aria-live="polite">
        {fc.error ? <p className="notice">{fc.error === "no forecast available for that day"
            ? "No forecast was published before this cut-off for that day. Try a later cut-off or another day." : fc.error}</p>
          : fc.loading || acc.loading || !s ? <p className="muted">Loading forecast…</p>
          : (<>
              <p className="statement">
                For {prettyDay(day)}, the latest forecast you could use averages <strong>{mw(avgForecast)} MW</strong> of wind.
                Over the month, that kind of forecast overshot actual wind by more than <strong>{mw(shortfall)} MW</strong> in only 1 half-hour out of 20, so cover that much from thermal or other sources if you want to be safe.
              </p>
              <p className="muted">Forecast last updated {dayTime(fc.data.latest_publish_time)}. Using the forecast available at {cutoff} on the day before.</p>
            </>)}
      </section>

      <section>
        <h2>Forecast against actual</h2>
        {pts && s && <DayChart points={pts} errLow={s.error_p05_mw} errHigh={s.error_p95_mw} />}
        <p className="note">Shaded area: where actual wind landed 90% of the time over the month. Dashed line: the forecast minus the shortfall you should cover. Actual is shown only once it has been published.</p>
      </section>

      {s && (
        <section>
          <h2>How accurate is the forecast?</h2>
          <p className="note">Based on {s.n.toLocaleString("en-GB")} half-hours in January, using the forecast available at {cutoff} the day before.</p>
          <dl className="facts">
            <div><dt>Typical miss</dt><dd>{mw(s.mae_mw)} MW<small>mean absolute error ({mw(s.nmae_pct, 1)}% of average wind)</small></dd></div>
            <div><dt>Large miss</dt><dd>{mw(s.rmse_mw)} MW<small>root mean squared error, weights big misses more</small></dd></div>
            <div><dt>Lean</dt><dd>{s.bias_mw > 0 ? "+" : ""}{mw(s.bias_mw)} MW<small>{s.bias_mw > 0 ? "forecast runs high on average" : "forecast runs low on average"}</small></dd></div>
            <div><dt>9 in 10 within</dt><dd>{mw(s.abs_error_p90_mw)} MW<small>of the forecast; 19 in 20 within {mw(s.abs_error_p95_mw)} MW</small></dd></div>
            <div><dt>Too high</dt><dd>{mw(s.over_forecast_share_pct)}%<small>of half-hours the forecast was above actual</small></dd></div>
            <div><dt>Steady lean vs random miss</dt><dd>{mw(s.mae_after_bias_mw)} MW<small>typical miss left after removing the lean of {mw(s.bias_mw)} MW. The lean is a consistent gap you can correct for; the rest is genuine uncertainty.</small></dd></div>
            <div><dt>Percentage error</dt><dd>{s.mape_pct == null ? "n/a" : `${mw(s.mape_pct, 1)}%`}<small>MAPE, ignoring periods under 100 MW of wind</small></dd></div>
          </dl>
        </section>
      )}

      {acc.data && err.data && (
        <section className="grid">
          <div><h3>Spread of errors</h3><p className="note">Forecast minus actual, MW. Right of the line means too high.</p><ErrorHistogram bins={err.data.bins} /></div>
          <div><h3>Average error by hour of day</h3><p className="note">When is the forecast weakest?</p><HourChart rows={acc.data.by_hour} /></div>
          <div><h3>Average error by day</h3><p className="note">Dashed line is the day you picked.</p><DayTrend rows={acc.data.by_day} selected={day} /></div>
          <div><h3>Error against how early the forecast was made</h3><p className="note">Hours before the target time, all published forecasts.</p><HorizonChart rows={acc.data.by_horizon} /></div>
        </section>
      )}

      {acc.error && <p className="notice">Could not load accuracy: {acc.error}</p>}
      <footer>Data: Elexon BMRS (FUELHH actual wind, WINDFOR forecast wind). Error = forecast minus actual.</footer>
    </main>
  );
}
