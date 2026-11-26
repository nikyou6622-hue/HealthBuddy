export function getApiBase(): string {
  if (typeof window === "undefined") {
    return (
      process.env.BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://127.0.0.1:8000"
    );
  }
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  // Standalone local Next.js dev server (without `vercel dev` proxy)
  if (window.location.port === "3006" || window.location.port === "3005") {
    return "http://127.0.0.1:8000";
  }
  // On Vercel / vercel dev, `/api/(.*)` is routed to the backend service on the same origin
  return "";
}

export const API_BASE = getApiBase();

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const base = getApiBase();
  const url = base ? new URL(path, base).toString() : path;
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    if (Array.isArray(errBody.detail)) {
      const msg = errBody.detail
        .map((d: any) => `${(d.loc || []).slice(-1)[0] || "input"}: ${d.msg}`)
        .join(" | ");
      throw new Error(msg);
    }
    throw new Error(errBody.detail ? String(errBody.detail) : `HTTP ${res.status}`);
  }
  return res.json();
}
