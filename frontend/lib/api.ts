export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
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

