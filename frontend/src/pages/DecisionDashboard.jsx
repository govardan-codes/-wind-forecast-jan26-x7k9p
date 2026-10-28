import { useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getDecision } from "../api";
import MetricCard from "../components/MetricCard.jsx";
import { fmt, hhmm, shortDateTime } from "../format";
import { useApi } from "../useApi";

export default function DecisionDashboard() {
  const [date, setDate] = useState("2026-01-15");
  const { data, error, loading } = useApi(() => getDecision(date), date);

  const rows = useMemo(
    () => (data ? data.points.map((p) => ({ ...p, time: hhmm(p.startTime) })) : []),
    [data]
  );
  const s = data?.summary;

  return (
    <>
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Decision Dashboard</h1>
          <p className="max-w-2xl text-sm text-slate-600">
            For a delivery day, the wind forecast the desk could actually see when committing in the day-ahead market,
            compared with what wind really delivered.
          </p>
        </div>
        <label className="text-sm font-medium">
          Delivery date
          <input
            type="date"
            min="2026-01-01"
            max="2026-01-31"
            value={date}
            onChange={(e) => e.target.value && setDate(e.target.value)}
            className="mt-1 block rounded-md border border-slate-300 bg-white px-3 py-1.5"
          />
        </label>
      </section>

      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {loading && !error && <div className="text-sm text-slate-500">Loading...</div>}

      {data && (
        <>
          <p className="text-xs text-slate-500">Rule applied: {data.cutoffRule}. Times are UTC (= UK time in January).</p>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard label="Forecast energy" value={fmt(s.forecastMwh)} unit="MWh" hint={`${s.slotsWithForecast}/48 slots`} />
            <MetricCard label="Actual energy" value={fmt(s.actualMwh)} unit="MWh" hint={`${s.slotsWithActual}/48 slots`} />
            <MetricCard
              label="Extra procurement needed"
              value={fmt(s.shortfallMwh)}
              unit="MWh"
              tone={s.shortfallMwh > 0 ? "red" : "green"}
              hint="Sum of slots where wind under-delivered"
            />
            <MetricCard
              label="Net gap (actual - forecast)"
              value={fmt(s.netGapMwh)}
              unit="MWh"
              tone={s.netGapMwh < 0 ? "red" : "green"}
              hint={`Surplus slots: +${fmt(s.surplusMwh)} MWh`}
            />
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="mb-3 font-medium">Actual vs latest day-ahead forecast (MW)</h2>
            <div className="h-80">
              <ResponsiveContainer>
                <LineChart data={rows} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" interval={3} />
                  <YAxis tickFormatter={(v) => fmt(v)} />
                  <Tooltip formatter={(v) => (v === null ? "-" : `${fmt(v, 1)} MW`)} />
                  <Legend />
                  <Line type="monotone" dataKey="forecast" name="Forecast (at decision time)" stroke="#0ea5e9" strokeWidth={2} dot={false} connectNulls />
                  <Line type="monotone" dataKey="actual" name="Actual" stroke="#16a34a" strokeWidth={2} dot={false} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h2 className="font-medium">Half-hourly gap</h2>
            <p className="mb-3 text-xs text-slate-500">
              Gap = Actual - Forecast. A negative gap means wind fell short of the forecast, so that power must be bought elsewhere
              (e.g. thermal); a positive gap means a surplus.
            </p>
            <div className="max-h-96 overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-100 text-left text-xs uppercase text-slate-600">
                  <tr>
                    <th className="px-3 py-2">Slot (UTC)</th>
                    <th className="px-3 py-2 text-right">Forecast MW</th>
                    <th className="px-3 py-2">Forecast published</th>
                    <th className="px-3 py-2 text-right">Actual MW</th>
                    <th className="px-3 py-2 text-right">Gap MW</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.startTime} className="border-t border-slate-100">
                      <td className="px-3 py-1.5">{r.time}</td>
                      <td className="px-3 py-1.5 text-right">{fmt(r.forecast, 1)}</td>
                      <td className="px-3 py-1.5 text-slate-500">{r.publishTime ? shortDateTime(r.publishTime) : "-"}</td>
                      <td className="px-3 py-1.5 text-right">{fmt(r.actual, 1)}</td>
                      <td className={`px-3 py-1.5 text-right font-medium ${r.gap === null ? "" : r.gap < 0 ? "text-red-600" : "text-emerald-600"}`}>
                        {r.gap === null ? "-" : `${r.gap > 0 ? "+" : ""}${fmt(r.gap, 1)}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  );
}
