export interface RecoReason {
  en: string;
  hi: string;
}

export interface RecoItem {
  id: string;
  category: "foods" | "exercises" | "hospitals" | "specialties" | "care";
  name: string;
  hindi: string;
  rank: number;
  score: number;
  status_label: string;
  needs_medical_clearance: boolean;
  reasons: RecoReason[];
  confidence: "high" | "medium" | "low_confidence";
  safety_notes: string;
  meta: Record<string, any>;
}

export interface RecoResponse {
  emergency: Record<string, any> | null;
  top_condition?: string | null;
  top_tier?: string | null;
  followup_days: number;
  categories: {
    foods: RecoItem[];
    exercises: RecoItem[];
    hospitals: RecoItem[];
    specialties: RecoItem[];
    care: RecoItem[];
  };
  confidence: "high" | "medium" | "low_confidence";
  missing_inputs: string[];
  model_version: string;
  disclaimer: string;
}

export interface RecoModelInfo {
  model_version: string;
  trained_at?: string | null;
  n_profiles?: number;
  artifact_size_mb?: number;
  models: Record<string, Record<string, number>>;
  limitations: string;
}

export interface RecoFeedbackPayload {
  item_id: string;
  category: "foods" | "exercises" | "hospitals" | "specialties" | "care";
  helpful: boolean;
  consent_data_storage?: boolean;
}

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
