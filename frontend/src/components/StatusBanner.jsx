import { useEffect, useState } from "react";
import { getHealth } from "../api";

// Polls /api/health: shows loading/error states and flags synthetic demo data.
export default function StatusBanner() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let timer;
    let cancelled = false;
    const poll = async () => {
      try {
        const h = await getHealth();
        if (cancelled) return;
        setHealth(h);
        if (h.status === "loading") timer = setTimeout(poll, 3000);
      } catch {
        if (!cancelled) {
          setHealth({ status: "unreachable" });
          timer = setTimeout(poll, 5000);
        }
      }
    };
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  if (!health || (health.status === "ready" && health.source !== "sample")) return null;
  const msg = {
    loading: "Loading wind data from Elexon (first start only, then cached)...",
    error: `Data failed to load: ${health.error}`,
    unreachable: "Cannot reach the API. Is the backend running?",
    ready: "Showing SYNTHETIC demo data (DATA_SOURCE=sample), not real Elexon data.",
  }[health.status];
  const color = health.status === "ready" ? "bg-amber-100 text-amber-900" : health.status === "loading" ? "bg-sky-100 text-sky-900" : "bg-red-100 text-red-900";
  return <div className={`px-4 py-2 text-center text-sm ${color}`}>{msg}</div>;
}
