import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import StatusBanner from "./components/StatusBanner.jsx";
import DecisionDashboard from "./pages/DecisionDashboard.jsx";
import AccuracyDashboard from "./pages/AccuracyDashboard.jsx";

const link = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium ${isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-200"}`;

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div>
            <div className="text-lg font-semibold">Gridbricks <span className="text-emerald-600">Wind Desk</span></div>
            <div className="text-xs text-slate-500">GB day-ahead procurement support - Elexon wind, January 2026</div>
          </div>
          <nav className="flex gap-2">
            <NavLink to="/decision" className={link}>Decision Dashboard</NavLink>
            <NavLink to="/accuracy" className={link}>Accuracy Dashboard</NavLink>
          </nav>
        </div>
      </header>
      <StatusBanner />
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        <Routes>
          <Route path="/" element={<Navigate to="/decision" replace />} />
          <Route path="/decision" element={<DecisionDashboard />} />
          <Route path="/accuracy" element={<AccuracyDashboard />} />
        </Routes>
      </main>
    </div>
  );
}
