export const fmt = (v, digits = 0) =>
  v === null || v === undefined ? "-" : Number(v).toLocaleString("en-GB", { maximumFractionDigits: digits, minimumFractionDigits: digits });

export const hhmm = (iso) => new Date(iso).toISOString().slice(11, 16); // times are UTC (= UK time in January)
export const shortDateTime = (iso) => new Date(iso).toISOString().slice(5, 16).replace("T", " ");
