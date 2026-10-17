const BASE = import.meta.env.VITE_API_URL;

function errorMessage(data, status) {
  if (!data) return `Request failed (${status})`;
  if (typeof data.detail === "string") return data.detail;
  // FastAPI validation errors come as a list
  if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg).join(". ");
  return `Request failed (${status})`;
}

export async function ask(question, explain = true) {
  let res;
  try {
    res = await fetch(`${BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, explain }),
    });
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }

  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (res.status === 429) {
    const wait = res.headers.get("Retry-After");
    throw new Error(`Too many requests. Try again${wait ? ` in ${wait} seconds` : " shortly"}.`);
  }
  if (!res.ok) throw new Error(errorMessage(data, res.status));
  return data;
}