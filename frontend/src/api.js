// Same-origin by default (nginx / vite proxy). Set VITE_API_URL when the API is hosted elsewhere.
const BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`);
  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json()).detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return res.json();
}

export const getHealth = () => get("/api/health");
export const getDecision = (deliveryDate) => get("/api/decision", { deliveryDate });
export const getEvaluation = (month) => get("/api/evaluation", { month });
