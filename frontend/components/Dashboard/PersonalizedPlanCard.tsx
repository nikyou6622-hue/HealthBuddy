"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Building2,
  CalendarClock,
  ChevronDown,
  ChevronUp,
  Dumbbell,
  HelpCircle,
  PhoneCall,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  ThumbsDown,
  ThumbsUp,
  Utensils,
} from "lucide-react";
import { apiFetch, RecoItem, RecoModelInfo, RecoResponse } from "@/lib/api";
import { HospitalMap } from "@/components/map/HospitalMap";

interface PersonalizedPlanCardProps {
  data: RecoResponse | null;
  modelInfo: RecoModelInfo | null;
  loading: boolean;
  error: string | null;
  lang: "en" | "hi";
  t: Record<string, string>;
  onRetry: () => void;
  onAddLabs: () => void;
}

type RecoTab = "foods" | "exercises" | "hospitals" | "specialties" | "care";

const STATUS_STYLE: Record<string, string> = {
  eat_more: "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder",
  ok: "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder",
  low: "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder",
  watch: "bg-hb-modBg text-hb-modInk border-hb-modBorder",
  moderate: "bg-hb-modBg text-hb-modInk border-hb-modBorder",
  limit: "bg-hb-highBg text-hb-highInk border-hb-highBorder",
  avoid: "bg-hb-highBg text-hb-highInk border-hb-highBorder",
  ask_dietitian: "bg-hb-skipBg text-hb-skipInk border-hb-skipBorder",
};

export function PersonalizedPlanCard({
  data,
  modelInfo,
  loading,
  error,
  lang,
  t,
  onRetry,
  onAddLabs,
}: PersonalizedPlanCardProps) {
  const [tab, setTab] = useState<RecoTab>("foods");
  const [openWhyId, setOpenWhyId] = useState<string | null>(null);
  const [hospFilter, setHospFilter] = useState<"all" | "24x7" | "govt" | "private">("all");
  const [focusedHospId, setFocusedHospId] = useState<string | null>(null);
  const [feedbackMap, setFeedbackMap] = useState<Record<string, "up" | "down">>({});
  const [detailsOpen, setDetailsOpen] = useState(false);

  const sendFeedback = async (item: RecoItem, helpful: boolean) => {
    setFeedbackMap((prev) => ({ ...prev, [item.id]: helpful ? "up" : "down" }));
    try {
      await apiFetch("/api/v1/reco/feedback", {
        method: "POST",
        body: JSON.stringify({
          item_id: item.id,
          category: item.category,
          helpful,
          consent_data_storage: false,
        }),
      });
    } catch {
      // Non-blocking feedback
    }
  };

  // Emergency takeover
  if (data?.emergency?.emergency) {
    return (
      <section
        id="sec-reco"
        role="alert"
        className="scroll-mt-24 rounded-2xl bg-red-700 text-white p-6 shadow-md space-y-3"
      >
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-7 h-7 shrink-0" aria-hidden="true" />
          <h2 className="text-lg font-extrabold">
            {t.emergency_title || "Immediate Emergency Action Required"}
          </h2>
        </div>
        <p className="text-sm text-red-50">
          {data.emergency.message || "Call emergency services immediately (112 / 108). Personalized recommendations are suppressed for safety."}
        </p>
        <a
          href="tel:112"
          className="inline-flex items-center gap-2 min-h-[44px] px-5 py-2.5 rounded-full bg-white text-red-800 font-extrabold text-sm"
        >
          <PhoneCall className="w-4 h-4" />
          <span>{t.call_112 || "Call 112 / 108"}</span>
        </a>
      </section>
    );
  }

  const tabs: { key: RecoTab; label: string; Icon: React.ComponentType<{ className?: string }> }[] = [
    { key: "foods", label: t.reco_tab_food || "Food", Icon: Utensils },
    { key: "exercises", label: t.reco_tab_exercise || "Exercise", Icon: Dumbbell },
    { key: "hospitals", label: t.reco_tab_hospitals || "Hospitals", Icon: Building2 },
    { key: "specialties", label: t.reco_tab_doctors || "Doctor & Tests", Icon: Stethoscope },
    { key: "care", label: t.reco_tab_followup || "Follow-up", Icon: CalendarClock },
  ];

  const items = data?.categories?.[tab] || [];
  const filteredHospitals =
    tab === "hospitals"
      ? items.filter((h) => {
          if (hospFilter === "24x7") return Boolean(h.meta?.emergency_24x7);
          const notes = `${h.meta?.insurance_notes || ""} ${h.name}`.toLowerCase();
          const isGovt = notes.includes("public") || notes.includes("cghs") || notes.includes("aiims") || notes.includes("pgimer");
          if (hospFilter === "govt") return isGovt;
          if (hospFilter === "private") return !isGovt;
          return true;
        })
      : items;

  const displayList = tab === "hospitals" ? filteredHospitals : items;
  const mapHospitals =
    tab === "hospitals"
      ? (focusedHospId
          ? [
              ...displayList.filter((h) => h.id === focusedHospId),
              ...displayList.filter((h) => h.id !== focusedHospId),
            ]
          : displayList
        ).map((h, idx) => ({
          id: idx + 1,
          name: h.name,
          city: String(h.meta?.city || ""),
          lat: h.meta?.lat ?? null,
          lon: h.meta?.lon ?? null,
        }))
      : [];

  return (
    <section
      id="sec-reco"
      aria-label={t.reco_title || "Personalized Plan (ML #3)"}
      className="scroll-mt-24 rounded-2xl bg-hb-surface border border-hb-border shadow-sm p-5 sm:p-6 space-y-5"
    >
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-hb-accentSoft text-hb-accentInk flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-extrabold text-hb-ink">
                {t.reco_title || "Personalized Plan (ML #3)"}
              </h2>
              {data?.model_version && (
                <span className="px-2 py-0.5 rounded-full bg-hb-subtle border border-hb-border text-[10px] font-bold text-hb-muted">
                  {data.model_version}
                </span>
              )}
            </div>
            <p className="text-xs text-hb-muted">
              {t.reco_subtitle || "Ranked recommendations tailored to your vitals, risk tiers, and labs"}
            </p>
          </div>
        </div>

        {data && (
          <span
            className={`shrink-0 whitespace-nowrap px-2.5 py-1 rounded-full text-[11px] font-extrabold border ${
              data.confidence === "low_confidence"
                ? "bg-hb-modBg text-hb-modInk border-hb-modBorder"
                : "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder"
            }`}
          >
            {data.confidence === "low_confidence" ? "Low Confidence" : data.confidence === "medium" ? "Medium Confidence" : "High Confidence"}
          </span>
        )}
      </div>

      {/* Missing labs / Low-confidence banner */}
      {data && (data.missing_inputs?.length > 0 || data.confidence === "low_confidence") && (
        <div className="rounded-xl bg-hb-modBg/60 border border-hb-modBorder p-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-hb-modInk space-y-0.5">
            <div className="font-extrabold">
              {data.confidence === "low_confidence"
                ? t.reco_low_conf || "Low confidence — more than half of lab inputs are missing or borderline."
                : t.reco_add_labs_prompt || "Add lab values to personalize this"}
            </div>
            {data.missing_inputs?.length > 0 && (
              <div className="opacity-90">
                Missing: {data.missing_inputs.slice(0, 5).join(", ")}
                {data.missing_inputs.length > 5 ? ` (+${data.missing_inputs.length - 5})` : ""}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onAddLabs}
            className="min-h-[38px] px-3.5 py-1.5 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-xs font-extrabold focus:outline-none focus:ring-2 focus:ring-hb-accent"
          >
            {t.add_lab_values || "Add lab values"}
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3" aria-busy="true">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-28 rounded-xl bg-hb-subtle border border-hb-border p-4 animate-pulse" />
          ))}
        </div>
      )}

      {/* Inline error with retry */}
      {!loading && error && (
        <div role="alert" className="rounded-xl bg-hb-highBg border border-hb-highBorder p-4 flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-bold text-hb-highInk">{error}</span>
          <button
            type="button"
            onClick={onRetry}
            className="min-h-[38px] px-3.5 py-1.5 rounded-full bg-hb-surface border border-hb-highBorder text-xs font-bold text-hb-highInk inline-flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{t.reco_retry || "Retry"}</span>
          </button>
        </div>
      )}

      {/* Empty state if no data yet */}
      {!loading && !error && !data && (
        <div className="rounded-xl bg-hb-subtle border border-hb-border p-5 text-center space-y-2.5">
          <p className="text-sm font-bold text-hb-ink">
            {t.reco_add_labs_prompt || "Add lab values to personalize this"}
          </p>
          <button
            type="button"
            onClick={onAddLabs}
            className="min-h-[40px] px-4 py-2 rounded-full bg-hb-cta text-hb-ctaInk text-xs font-extrabold"
          >
            {t.add_lab_values || "Add lab values"}
          </button>
        </div>
      )}

      {/* Tabs + Ranked Items */}
      {!loading && !error && data && (
        <>
          <div
            role="tablist"
            aria-label="Personalized plan categories"
            className="flex flex-nowrap overflow-x-auto no-scrollbar items-center gap-4 border-b border-hb-border"
          >
            {tabs.map(({ key, label, Icon }) => {
              const active = tab === key;
              return (
                <button
                  key={key}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setTab(key)}
                  className={`min-h-[44px] px-1 py-2.5 text-sm font-bold whitespace-nowrap inline-flex items-center gap-2 border-b-2 -mb-px focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                    active
                      ? "border-hb-accent text-hb-ink"
                      : "border-transparent text-hb-muted hover:text-hb-ink"
                  }`}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  <span>{label}</span>
                </button>
              );
            })}
          </div>

          {/* Hospital filters */}
          {tab === "hospitals" && (
            <div className="flex flex-nowrap overflow-x-auto no-scrollbar gap-1.5 pb-1">
              {(
                [
                  ["all", "All"],
                  ["24x7", "24x7"],
                  ["govt", "Government"],
                  ["private", "Private"],
                ] as const
              ).map(([fk, flbl]) => (
                <button
                  key={fk}
                  type="button"
                  onClick={() => setHospFilter(fk)}
                  className={`min-h-[36px] px-3 py-1 rounded-full text-xs font-bold border ${
                    hospFilter === fk
                      ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                      : "bg-hb-subtle text-hb-muted border-hb-border"
                  }`}
                >
                  {flbl}
                </button>
              ))}
            </div>
          )}

          <div role="tabpanel" className={tab === "hospitals" ? "grid grid-cols-1 lg:grid-cols-12 gap-4 items-start" : "space-y-3"}>
            <div className={tab === "hospitals" ? "lg:col-span-7 grid grid-cols-1 gap-3" : "grid grid-cols-1 md:grid-cols-2 gap-3.5 items-stretch"}>
              {displayList.map((item) => {
                const chipCls = STATUS_STYLE[item.status_label] || "bg-hb-subtle text-hb-ink border-hb-border";
                const isWhyOpen = openWhyId === item.id;
                const fb = feedbackMap[item.id];
                return (
                  <article
                    key={item.id}
                    className="h-full rounded-xl bg-hb-subtle border border-hb-border p-4 gap-3 flex flex-col justify-between transition-colors hover:border-hb-accent/50"
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2.5">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start gap-2">
                            <span className="shrink-0 mt-0.5 px-2 py-0.5 rounded-full bg-hb-surface border border-hb-border text-[10px] font-extrabold tabular-nums text-hb-muted">
                              #{item.rank}
                            </span>
                            <h3 className="text-sm font-extrabold text-hb-ink leading-snug line-clamp-2">
                              {lang === "hi" && item.hindi ? item.hindi : item.name}
                            </h3>
                          </div>
                          {lang === "en" && item.hindi && item.hindi !== item.name && (
                            <p className="text-[11px] text-hb-muted mt-1 pl-8">{item.hindi}</p>
                          )}
                        </div>
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border shrink-0 whitespace-nowrap ${chipCls}`}>
                          {item.status_label.replace(/_/g, " ")}
                        </span>
                      </div>

                      {item.needs_medical_clearance && (
                        <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-hb-highBg text-hb-highInk border border-hb-highBorder text-[10px] font-bold">
                          <AlertTriangle className="w-3 h-3 shrink-0" aria-hidden="true" />
                          <span>{t.reco_clearance || "Medical clearance advised"}</span>
                        </div>
                      )}

                      {item.safety_notes && (
                        <p className="text-[11px] text-hb-muted leading-relaxed">{item.safety_notes}</p>
                      )}
                    </div>

                    <div className="mt-auto pt-2.5 border-t border-hb-border flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setOpenWhyId(isWhyOpen ? null : item.id)}
                          aria-expanded={isWhyOpen}
                          className="min-h-[34px] px-2.5 py-1 rounded-full bg-hb-surface hover:bg-hb-accentSoft border border-hb-border text-[11px] font-bold text-hb-ink inline-flex items-center gap-1"
                        >
                          <HelpCircle className="w-3.5 h-3.5" aria-hidden="true" />
                          <span>{t.reco_why || "Why?"}</span>
                        </button>
                        {tab === "hospitals" && (
                          <button
                            type="button"
                            onClick={() => setFocusedHospId(item.id)}
                            className="min-h-[34px] px-2.5 py-1 rounded-full bg-hb-surface border border-hb-border text-[11px] font-bold text-hb-ink"
                          >
                            {t.open_map || "Open map"}
                          </button>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          aria-label={`Helpful: ${item.name}`}
                          onClick={() => sendFeedback(item, true)}
                          className={`w-8 h-8 rounded-full border flex items-center justify-center transition-colors ${
                            fb === "up"
                              ? "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder"
                              : "bg-hb-surface text-hb-muted border-hb-border hover:text-hb-ink"
                          }`}
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          aria-label={`Not helpful: ${item.name}`}
                          onClick={() => sendFeedback(item, false)}
                          className={`w-8 h-8 rounded-full border flex items-center justify-center transition-colors ${
                            fb === "down"
                              ? "bg-hb-highBg text-hb-highInk border-hb-highBorder"
                              : "bg-hb-surface text-hb-muted border-hb-border hover:text-hb-ink"
                          }`}
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {isWhyOpen && (
                      <div className="rounded-lg bg-hb-surface border border-hb-border p-3 space-y-1 text-xs text-hb-ink">
                        <div className="font-extrabold text-[11px] uppercase tracking-wider text-hb-muted">
                          Top 3 Reasons (score: {(item.score * 100).toFixed(0)}%)
                        </div>
                        <ul className="list-disc list-inside space-y-0.5">
                          {item.reasons.map((r, idx) => (
                            <li key={idx}>{lang === "hi" ? r.hi : r.en}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>

            {tab === "hospitals" && (
              <div className="lg:col-span-5 lg:sticky lg:top-20">
                <HospitalMap hospitals={mapHospitals} />
              </div>
            )}
          </div>
        </>
      )}

      {/* Model details accordion */}
      <div className="pt-2 border-t border-hb-border">
        <button
          type="button"
          onClick={() => setDetailsOpen((v) => !v)}
          aria-expanded={detailsOpen}
          className="w-full min-h-[40px] flex items-center justify-between text-xs font-bold text-hb-muted hover:text-hb-ink"
        >
          <span className="inline-flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-hb-accentInk" aria-hidden="true" />
            <span>{t.reco_model_details || "Model details & honest limitations"}</span>
          </span>
          {detailsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {detailsOpen && modelInfo && (
          <div className="mt-3 rounded-xl bg-hb-subtle border border-hb-border p-4 space-y-3 text-xs">
            <p className="text-hb-muted leading-relaxed">{modelInfo.limitations}</p>
            {modelInfo.models?.hist_gradient_boosting && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse tabular-nums">
                  <thead>
                    <tr className="border-b border-hb-border text-[11px] uppercase text-hb-muted">
                      <th className="py-1.5 pr-3">Model</th>
                      <th className="py-1.5 pr-3">NDCG@5</th>
                      <th className="py-1.5 pr-3">NDCG@10</th>
                      <th className="py-1.5 pr-3">Precision@10</th>
                      <th className="py-1.5 pr-3">MAP</th>
                      <th className="py-1.5">Safety Violations (Post)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(modelInfo.models).map(([mName, m]) => (
                      <tr key={mName} className="border-b border-hb-border/50">
                        <td className="py-1.5 pr-3 font-bold text-hb-ink">{mName}</td>
                        <td className="py-1.5 pr-3">{m.ndcg_at_5}</td>
                        <td className="py-1.5 pr-3 font-bold">{m.ndcg_at_10}</td>
                        <td className="py-1.5 pr-3">{m.precision_at_10}</td>
                        <td className="py-1.5 pr-3">{m.map}</td>
                        <td className="py-1.5">{m.safety_violation_rate_post_filter}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

