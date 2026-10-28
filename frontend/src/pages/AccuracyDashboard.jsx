import { useMemo } from "react";
import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import { getEvaluation } from "../api";
import MetricCard from "../components/MetricCard.jsx";
import { fmt, shortDateTime } from "../format";
import { useApi } from "../useApi";

const MONTH = "2026-01";

export default function AccuracyDashboard() {
  const { data, error, loading } = useApi(() => getEvaluation(MONTH), MONTH);
  const m = data?.metrics;

  const slots = useMemo(() => data?.slots ?? [], [data]);
  const maxVal = useMemo(() => Math.ceil(Math.max(0, ...slots.map((s) => Math.max(s.actual, s.forecast))) / 1000) * 1000, [slots]);

  return (
    <>
      <section>
        <h1 className="text-xl font-semibold">Accuracy Dashboard - {MONTH}</h1>
        <p className="max-w-3xl text-sm text-slate-600">
          How good were the forecasts that were actually available at decision time? Error = Actual - Forecast, so a
          negative bias means the forecasts were too optimistic (wind under-delivered).
        </p>
      </section>

      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {loading && !error && <div className="text-sm text-slate-500">Loading...</div>}

      {m && m.count > 0 && (
        <>
          <p className="text-xs text-slate-500">Rule applied: {data.cutoffRule}. {m.count} half-hour slots evaluated.</p>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <MetricCard label="MAE" value={fmt(m.mae, 0)} unit="MW" hint="Average miss size" />
            <MetricCard label="RMSE" value={fmt(m.rmse, 0)} unit="MW" hint="Penalises large misses" />
            <MetricCard label="MAPE" value={fmt(m.mape, 1)} unit="%" hint={`Excludes ${m.count - m.mapeCount} zero-wind slots`} />
            <MetricCard
              label="Bias"
              value={`${m.bias > 0 ? "+" : ""}${fmt(m.bias, 0)}`}
              unit="MW"
              tone={Math.abs(m.bias) < 0.05 * m.mae ? "green" : m.bias < 0 ? "red" : "amber"}
              hint={m.bias < 0 ? "Forecasts too high on average" : "Forecasts too low on average"}
            />
            <MetricCard label="MAE vs mean wind" value={fmt(m.nmae, 1)} unit="%" hint={`Mean actual ${fmt(m.meanActual)} MW`} />
          </section>

          <section className="rounded-xl border border-sky-100 bg-sky-50 p-4 text-sm text-sky-900">
            <strong>What this means for the desk:</strong> day-ahead wind forecasts missed by about {fmt(m.mae, 0)} MW on average
            ({fmt(m.nmae, 1)}% of typical output), with larger misses reaching around {fmt(m.rmse, 0)} MW (RMSE). Consider
            holding a procurement buffer of this order when relying on the forecast.
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="mb-3 font-medium">Forecast error over time (MW, actual - forecast)</h2>
            <div className="h-72">
              <ResponsiveContainer>
                <LineChart data={slots} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="startTime" interval={47} tickFormatter={(v) => v.slice(5, 10)} />
                  <YAxis tickFormatter={(v) => fmt(v)} />
                  <Tooltip labelFormatter={shortDateTime} formatter={(v) => `${fmt(v, 0)} MW`} />
                  <ReferenceLine y={0} stroke="#64748b" />
                  <Line type="monotone" dataKey="error" name="Error" stroke="#e11d48" strokeWidth={1} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="mb-3 font-medium">Forecast vs actual (MW) - points on the line are perfect forecasts</h2>
            <div className="h-96">
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="forecast" name="Forecast" domain={[0, maxVal]} tickFormatter={(v) => fmt(v)} label={{ value: "Forecast (MW)", position: "insideBottom", offset: -10 }} />
                  <YAxis type="number" dataKey="actual" name="Actual" domain={[0, maxVal]} tickFormatter={(v) => fmt(v)} label={{ value: "Actual (MW)", angle: -90, position: "insideLeft" }} />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(v) => `${fmt(v, 0)} MW`} />
                  <ReferenceLine segment={[{ x: 0, y: 0 }, { x: maxVal, y: maxVal }]} stroke="#16a34a" strokeDasharray="6 4" />
                  <Scatter data={slots} fill="#0ea5e9" fillOpacity={0.45} isAnimationActive={false} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}
      {m && m.count === 0 && <div className="text-sm text-slate-600">No slots with both an actual and a day-ahead forecast.</div>}
    </>
  );
}
