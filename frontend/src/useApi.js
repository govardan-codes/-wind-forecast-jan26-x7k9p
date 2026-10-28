import { useEffect, useState } from "react";

/** Runs an async loader when `key` changes. Retries automatically while the backend reports it is still loading. */
export function useApi(loader, key) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    let timer;
    setState((s) => ({ ...s, loading: true, error: null }));
    const run = async () => {
      try {
        const data = await loader();
        if (!cancelled) setState({ data, error: null, loading: false });
      } catch (err) {
        if (cancelled) return;
        if (/still loading/i.test(err.message)) {
          setState({ data: null, error: "Backend is still loading Elexon data - retrying...", loading: true });
          timer = setTimeout(run, 3000);
        } else {
          setState({ data: null, error: err.message, loading: false });
        }
      }
    };
    run();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return state;
}
