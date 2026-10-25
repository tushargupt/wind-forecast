// Small fetch wrapper; throws Error with the API's message so the UI can show it.
async function get(path, params = {}) {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null));
  const res = await fetch(`/api/${path}?${qs}`);
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch { /* keep statusText */ }
    throw new Error(msg);
  }
  return res.json();
}

export const getForecast = (day, cutoff) => get("forecast", { day, cutoff });
export const getAccuracy = (cutoff, day) => get("accuracy", { cutoff, day });
export const getErrors = (cutoff) => get("errors", { cutoff });
