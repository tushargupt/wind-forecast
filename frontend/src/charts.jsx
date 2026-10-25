import {
  ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
  BarChart, Bar, ReferenceLine, LineChart,
} from "recharts";
import { clock, mw } from "./format.js";

const C = { forecast: "#1f5fbf", actual: "#14232b", band: "#1f5fbf", safe: "#b4540a", grid: "#d5dedb", bar: "#5d7f8a" };
const axis = { stroke: "#5b6b70", fontSize: 12, tickLine: false };

export function DayChart({ points, errLow, errHigh }) {
  // Actual = forecast - error, so a 90% band for actual is [f - p95, f - p05].
  const data = points.map((p) => ({
    time: clock(p.t),
    forecast: p.forecast_mw,
    actual: p.actual_mw,
    band: [Math.max(0, p.forecast_mw - errHigh), Math.max(0, p.forecast_mw - errLow)],
    safe: Math.max(0, p.forecast_mw - Math.max(0, errHigh)),
  }));
  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="time" {...axis} interval={5} />
        <YAxis {...axis} width={56} tickFormatter={(v) => `${v / 1000}k`} label={{ value: "MW", angle: -90, position: "insideLeft", fill: "#5b6b70", fontSize: 12 }} />
        <Tooltip formatter={(v, n) => (Array.isArray(v) ? `${mw(v[0])} to ${mw(v[1])} MW` : `${mw(v)} MW`)} />
        <Legend verticalAlign="top" height={30} />
        <Area dataKey="band" name="Likely range of actual wind (90%)" stroke="none" fill={C.band} fillOpacity={0.15} isAnimationActive={false} />
        <Line dataKey="safe" name="Safe level to plan on" stroke={C.safe} strokeDasharray="5 4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
        <Line dataKey="forecast" name="Forecast (at decision time)" stroke={C.forecast} dot={false} strokeWidth={2.5} isAnimationActive={false} />
        <Line dataKey="actual" name="Actual" stroke={C.actual} dot={false} strokeWidth={1.5} connectNulls={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function ErrorHistogram({ bins }) {
  const data = bins.map((b) => ({ mid: Math.round((b.from + b.to) / 2), count: b.count }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="mid" {...axis} type="number" domain={["dataMin", "dataMax"]} tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`} />
        <YAxis {...axis} width={40} />
        <Tooltip labelFormatter={(v) => `Error about ${mw(v)} MW`} formatter={(v) => [v, "half-hours"]} />
        <ReferenceLine x={0} stroke={C.actual} />
        <Bar dataKey="count" fill={C.bar} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function HourChart({ rows }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="hour" {...axis} tickFormatter={(h) => `${String(h).padStart(2, "0")}h`} />
        <YAxis {...axis} width={44} />
        <Tooltip formatter={(v) => `${mw(v)} MW`} labelFormatter={(h) => `Hour starting ${String(h).padStart(2, "0")}:00`} />
        <Bar dataKey="mae_mw" name="Average error" fill={C.bar} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DayTrend({ rows, selected }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="day" {...axis} tickFormatter={(d) => d.slice(8)} />
        <YAxis {...axis} width={44} />
        <Tooltip formatter={(v) => `${mw(v)} MW`} />
        {selected && <ReferenceLine x={selected} stroke={C.safe} strokeDasharray="4 3" />}
        <Line dataKey="mae_mw" name="Average error" stroke={C.forecast} strokeWidth={2} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function HorizonChart({ rows, cutoffHorizonHint }) {
  const data = rows.map((r) => ({ label: `${r.horizon_from_h} to ${r.horizon_to_h}h`, mae_mw: r.mae_mw }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="label" {...axis} />
        <YAxis {...axis} width={44} />
        <Tooltip formatter={(v) => `${mw(v)} MW`} />
        <Bar dataKey="mae_mw" name="Average error" fill={C.bar} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
