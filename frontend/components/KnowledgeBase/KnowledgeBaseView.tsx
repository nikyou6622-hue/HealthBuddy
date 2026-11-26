"use client";

import React, { useEffect, useState } from "react";
import {
  BookOpen,
  Building2,
  CheckCircle2,
  Dumbbell,
  HeartPulse,
  Phone,
  Search,
  ShieldCheck,
  Stethoscope,
  Utensils,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

interface KnowledgeBaseViewProps {
  t: Record<string, string>;
  onAskHealthBuddy: () => void;
}

type KbCategory = "all" | "hospitals" | "doctors" | "guidance" | "care" | "foods" | "exercises";

export function KnowledgeBaseView({ t, onAskHealthBuddy }: KnowledgeBaseViewProps) {
  const [category, setCategory] = useState<KbCategory>("all");
  const [query, setQuery] = useState("");
  const [kb, setKb] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadKb = async (cat: KbCategory, q: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (cat !== "all") params.set("category", cat);
      if (q.trim()) params.set("q", q.trim());
      const qs = params.toString();
      const res = await apiFetch<any>(`/api/v1/kb${qs ? `?${qs}` : ""}`);
      setKb(res);
    } catch {
      setError("Could not load Knowledge Base records from the backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKb(category, query);
  }, [category]);

  const counts = kb?.counts || { hospitals: 0, doctors: 0, guidance: 0, care: 0, total: 0 };

  return (
    <div className="space-y-5">
      {/* Header & Search */}
      <div className="rounded-lg bg-hb-surface border border-hb-border shadow-sm p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md bg-hb-accentSoft text-hb-ink flex items-center justify-center shrink-0">
              <BookOpen className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-hb-ink">
                {t.nav_kb || "Clinical Knowledge Base"}
              </h2>
              <p className="text-xs text-hb-muted tabular-nums">
                {counts.total} verified records across hospitals, doctors, clinical guidance, and care services
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onAskHealthBuddy}
            className="min-h-[40px] px-4 py-2 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-xs font-extrabold inline-flex items-center gap-2 shadow-sm"
          >
            <img src="/healthbuddy-logo.svg" alt="" className="w-4 h-4" aria-hidden="true" />
            <span>{t.ask_healthbuddy || "Ask HealthBuddy"}</span>
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadKb(category, query);
          }}
          className="flex flex-wrap gap-2"
        >
          <div className="relative flex-1 min-w-[220px]">
            <Search className="w-4 h-4 text-hb-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search hospitals, specialists, diets, tests, or services..."
              aria-label="Search knowledge base"
              className="w-full min-h-[42px] pl-10 pr-4 py-2 rounded-full bg-hb-canvas border border-hb-border text-sm text-hb-ink focus:outline-none focus:ring-2 focus:ring-hb-accent"
            />
          </div>
          <button
            type="submit"
            className="min-h-[42px] px-4 py-2 rounded-full bg-hb-subtle hover:bg-hb-border/50 border border-hb-border text-xs font-bold text-hb-ink"
          >
            Search KB
          </button>
        </form>

        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Knowledge base categories">
          {(
            [
              ["all", "All Records", counts.total],
              ["hospitals", "Hospitals", counts.hospitals],
              ["doctors", "Doctors & Specialists", counts.doctors],
              ["guidance", "Guidance", counts.guidance],
              ["care", "Care & Services", counts.care],
              ["foods", "Indian Foods", counts.foods || 0],
              ["exercises", "Exercises & Yoga", counts.exercises || 0],
            ] as const
          ).map(([key, label, count]) => (
            <button
              key={key}
              type="button"
              onClick={() => setCategory(key)}
              aria-pressed={category === key}
              className={`min-h-[38px] px-3.5 py-1.5 rounded-full text-xs font-bold border inline-flex items-center gap-1.5 transition-colors ${
                category === key
                  ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                  : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
              }`}
            >
              <span>{label}</span>
              <span className="tabular-nums text-[11px] opacity-80">({count})</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div role="alert" className="rounded-md bg-hb-highBg border border-hb-highBorder p-4 text-xs font-bold text-hb-highInk">
          {error}
        </div>
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-busy="true">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-32 rounded-lg bg-hb-surface border border-hb-border p-4 animate-pulse" />
          ))}
        </div>
      )}

      {!loading && kb && (
        <div className="space-y-6">
          {/* HOSPITALS */}
          {kb.hospitals?.length > 0 && (
            <section className="space-y-3">
              <h3 className="text-base font-extrabold text-hb-ink inline-flex items-center gap-2">
                <Building2 className="w-4 h-4 text-hb-accent" aria-hidden="true" />
                <span>Verified Hospitals ({kb.hospitals.length})</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {kb.hospitals.map((h: any) => (
                  <article key={h.id} className="rounded-lg bg-hb-surface border border-hb-border p-4 shadow-sm space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-extrabold text-sm text-hb-ink">{h.name}</span>
                      <div className="flex gap-1.5">
                        <span className="px-2 py-0.5 rounded-full bg-hb-lowBg text-hb-lowInk border border-hb-lowBorder text-[11px] font-bold inline-flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" aria-hidden="true" /> Verified
                        </span>
                        {h.emergency_24x7 && (
                          <span className="px-2 py-0.5 rounded-full bg-hb-highBg text-hb-highInk border border-hb-highBorder text-[11px] font-bold">
                            24x7 Emergency
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-hb-muted">
                      {h.address}, {h.city} ({h.pincode})
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {(h.specialties || []).map((s: string) => (
                        <span key={s} className="px-2 py-0.5 rounded-full bg-hb-subtle border border-hb-border text-[11px] font-semibold text-hb-ink">
                          {s}
                        </span>
                      ))}
                    </div>
                    <div className="pt-2 border-t border-hb-border flex flex-wrap items-center justify-between gap-2 text-xs text-hb-muted">
                      <span>{h.insurance_notes}</span>
                      {h.phone && (
                        <span className="inline-flex items-center gap-1 font-bold text-hb-ink tabular-nums">
                          <Phone className="w-3 h-3" aria-hidden="true" /> {h.phone}
                        </span>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          {/* DOCTORS & SPECIALISTS */}
          {kb.doctors?.length > 0 && (
            <section className="space-y-3">
              <h3 className="text-base font-extrabold text-hb-ink inline-flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-hb-accent" aria-hidden="true" />
                <span>Doctors &amp; Specialists ({kb.doctors.length})</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {kb.doctors.map((d: any) => (
                  <article key={d.id} className="rounded-lg bg-hb-surface border border-hb-border p-4 shadow-sm space-y-2">
                    <div>
                      <div className="font-extrabold text-sm text-hb-ink">{d.name}</div>
                      <div className="text-xs text-hb-muted">{d.subspecialty}</div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {(d.conditions_covered || []).map((c: string) => (
                        <span key={c} className="px-2 py-0.5 rounded-full bg-hb-accentSoft text-hb-ink text-[11px] font-bold">
                          {c}
                        </span>
                      ))}
                    </div>
                    {d.available_at_hospitals?.length > 0 && (
                      <p className="text-[11px] text-hb-muted pt-1 border-t border-hb-border">
                        <strong>Available at:</strong> {d.available_at_hospitals.slice(0, 3).join(", ")}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}

          {/* GUIDANCE */}
          {kb.guidance?.length > 0 && (
            <section className="space-y-3">
              <h3 className="text-base font-extrabold text-hb-ink inline-flex items-center gap-2">
                <HeartPulse className="w-4 h-4 text-hb-accent" aria-hidden="true" />
                <span>Clinical Guidance ({kb.guidance.length})</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {kb.guidance.map((g: any) => {
                  const tierBadge =
                    g.tier === "high"
                      ? "bg-hb-highBg text-hb-highInk border-hb-highBorder"
                      : g.tier === "moderate"
                      ? "bg-hb-modBg text-hb-modInk border-hb-modBorder"
                      : "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder";
                  return (
                    <article key={g.id} className="rounded-lg bg-hb-surface border border-hb-border p-4 shadow-sm space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-extrabold text-sm text-hb-ink capitalize">
                          {g.condition} — {g.title}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase border ${tierBadge}`}>
                          {g.tier}
                        </span>
                      </div>
                      {g.exercise_target && (
                        <p className="text-xs text-hb-ink">
                          <strong>Activity:</strong> {g.exercise_target}
                        </p>
                      )}
                      {g.doctor_tests?.length > 0 && (
                        <p className="text-xs text-hb-muted">
                          <strong>Tests &amp; Care:</strong> {g.doctor_tests.slice(0, 2).join("; ")}
                        </p>
                      )}
                      <div className="pt-2 border-t border-hb-border flex flex-wrap justify-between gap-1 text-[11px] text-hb-muted">
                        <span>{g.source}</span>
                        <span>Follow-up: {g.followup_days}d</span>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          )}

          {/* CARE & SERVICES */}
          {kb.care?.length > 0 && (
            <section className="space-y-3">
              <h3 className="text-base font-extrabold text-hb-ink inline-flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-hb-accent" aria-hidden="true" />
                <span>Care Routing &amp; Clinical Services ({kb.care.length})</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {kb.care.map((c: any) => (
                  <article key={c.id} className="rounded-lg bg-hb-surface border border-hb-border p-3.5 shadow-sm space-y-1.5">
                    <div className="font-extrabold text-xs uppercase tracking-wide text-hb-ink">
                      {c.name}
                    </div>
                    <p className="text-xs text-hb-muted leading-snug">{c.description}</p>
                    {c.available_at_hospitals?.length > 0 && (
                      <p className="text-[11px] text-hb-muted pt-1 border-t border-hb-border">
                        {c.available_at_hospitals.slice(0, 3).join(", ")}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}
          {/* INDIAN FOODS */}
          {kb.foods?.length > 0 && (
            <section className="space-y-3">
              <h3 className="text-base font-extrabold text-hb-ink inline-flex items-center gap-2">
                <Utensils className="w-4 h-4 text-hb-accent" aria-hidden="true" />
                <span>Indian Food Knowledge Base ({kb.foods.length})</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {kb.foods.slice(0, category === "foods" ? 60 : 12).map((f: any) => (
                  <article key={f.id} className="rounded-lg bg-hb-surface border border-hb-border p-3.5 shadow-sm space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-extrabold text-xs text-hb-ink">{f.name}</div>
                        <div className="text-[11px] text-hb-muted">{f.hindi} · {f.group}</div>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-hb-subtle border border-hb-border text-[10px] font-bold uppercase text-hb-ink shrink-0">
                        {(f.advice || "").replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-hb-muted leading-snug">{f.note}</p>
                    {f.codes && (
                      <div className="flex flex-wrap gap-1 pt-1 border-t border-hb-border text-[10px] text-hb-muted">
                        <span>DM: <strong className="text-hb-ink">{f.codes.diabetes}</strong></span>
                        <span>· HTN: <strong className="text-hb-ink">{f.codes.hypertension}</strong></span>
                        <span>· Heart: <strong className="text-hb-ink">{f.codes.heart}</strong></span>
                        <span>· CKD: <strong className="text-hb-ink">{f.codes.kidney}</strong></span>
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}

          {/* EXERCISES & YOGA */}
          {kb.exercises?.length > 0 && (
            <section className="space-y-3">
              <h3 className="text-base font-extrabold text-hb-ink inline-flex items-center gap-2">
                <Dumbbell className="w-4 h-4 text-hb-accent" aria-hidden="true" />
                <span>Exercise &amp; Yoga Knowledge Base ({kb.exercises.length})</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {kb.exercises.slice(0, category === "exercises" ? 60 : 12).map((ex: any) => (
                  <article key={ex.id} className="rounded-lg bg-hb-surface border border-hb-border p-3.5 shadow-sm space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-extrabold text-xs text-hb-ink">{ex.name}</div>
                        <div className="text-[11px] text-hb-muted">{ex.hindi} · {ex.duration_or_reps}</div>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-hb-subtle border border-hb-border text-[10px] font-bold uppercase text-hb-ink shrink-0">
                        {ex.intensity}
                      </span>
                    </div>
                    <p className="text-xs text-hb-ink leading-snug">{ex.benefits}</p>
                    <p className="text-[11px] text-hb-muted leading-snug pt-1 border-t border-hb-border">{ex.cautions}</p>
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

