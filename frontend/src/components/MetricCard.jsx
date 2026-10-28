export default function MetricCard({ label, value, unit, hint, tone = "slate" }) {
  const tones = { slate: "text-slate-900", red: "text-red-600", green: "text-emerald-600", amber: "text-amber-600" };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${tones[tone]}`}>
        {value} {unit && <span className="text-sm font-normal text-slate-500">{unit}</span>}
      </div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}
