"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Ban,
  BookOpen,
  CalendarClock,
  CheckCircle2,
  Dumbbell,
  Search,
  Stethoscope,
  Utensils,
} from "lucide-react";
import { LocalizedPlan } from "@/lib/plans";
import { FollowUpList } from "@/components/Dashboard/FollowUpList";

interface GuidanceTabsProps {
  activeCondition: string;
  onSelectCondition: (c: string) => void;
  getConditionTier: (c: string) => string;
  activePlan: LocalizedPlan | null;
  followups: { condition: string; tier: string; due_date: string }[];
  kbGuidance?: any[];
  kbFaqs?: any[];
  kbFoods?: any[];
  kbExercises?: any[];
  lang: "en" | "hi";
  t: Record<string, string>;
  onSeeFullPlan: () => void;
  onDownloadPdf: () => void;
}

const CONDITIONS = ["heart", "diabetes", "hypertension", "obesity", "metabolic", "kidney"];

export function GuidanceTabs({
  activeCondition,
  onSelectCondition,
  getConditionTier,
  activePlan,
  followups,
  kbGuidance = [],
  kbFaqs = [],
  kbFoods = [],
  kbExercises = [],
  lang,
  t,
  onSeeFullPlan,
  onDownloadPdf,
}: GuidanceTabsProps) {
  const [tab, setTab] = useState<"food" | "exercise" | "tests" | "followup">("food");
  const [foodQuery, setFoodQuery] = useState("");
  const [foodFilter, setFoodFilter] = useState<"all" | "ok" | "avoid">("all");
  const [exerciseQuery, setExerciseQuery] = useState("");

  const activeTier = getConditionTier(activeCondition);
  const matchedKbGuide =
    kbGuidance.find((g) => g.condition === activeCondition && g.tier === activeTier) ||
    kbGuidance.find((g) => g.condition === activeCondition) ||
    null;

  const matchedFaqs = kbFaqs.filter((f) => {
    const tags = (f.tags || []).map((x: string) => x.toLowerCase());
    return (
      f.category === "guidance" ||
      tags.includes(activeCondition) ||
      (activeCondition === "hypertension" && tags.includes("bp")) ||
      (activeCondition === "obesity" && tags.includes("bmi"))
    );
  });

  return (
    <section
      id="sec-guidance"
      className="scroll-mt-24 rounded-2xl bg-hb-surface border border-hb-border shadow-sm p-5 sm:p-6 space-y-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-extrabold text-hb-ink">
            {t.sticky_guidance || "Guidance"} &amp; {t.sticky_followup || "Follow-up"}
          </h2>
          <p className="text-xs text-hb-muted">
            {activePlan ? `${activePlan.title} (${activePlan.tier} tier)` : "Condition-specific guidance"}
          </p>
        </div>

        <div className="flex flex-nowrap overflow-x-auto no-scrollbar sm:flex-wrap gap-1.5 pb-1 sm:pb-0 w-full sm:w-auto" role="group" aria-label="Select condition">
          {CONDITIONS.map((c) => {
            const tier = getConditionTier(c);
            const dotClass =
              tier === "high"
                ? "bg-hb-highInk"
                : tier === "moderate"
                ? "bg-hb-accent"
                : "bg-hb-lowInk";
            const isSelected = activeCondition === c;
            return (
              <button
                key={c}
                type="button"
                onClick={() => onSelectCondition(c)}
                aria-pressed={isSelected}
                className={`min-h-[38px] px-3 py-1.5 rounded-full text-xs font-bold capitalize border inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                  isSelected
                    ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                    : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${dotClass}`} aria-hidden="true" />
                <span>{c}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Underline Tab Bar */}
      <div
        role="tablist"
        aria-label="Guidance categories"
        className="flex flex-nowrap overflow-x-auto no-scrollbar items-center gap-4 border-b border-hb-border"
      >
        {(
          [
            ["food", t.sticky_food || "Food", Utensils],
            ["exercise", t.sticky_exercise || "Exercise", Dumbbell],
            ["tests", "Doctor & Lab Tests (KB)", Stethoscope],
            ["followup", t.sticky_followup || "Follow-up", CalendarClock],
          ] as const
        ).map(([key, label, Icon]) => {
          const isActive = tab === key;
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setTab(key)}
              className={`min-h-[44px] px-1 py-2.5 text-sm font-bold inline-flex items-center gap-2 border-b-2 -mb-px focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                isActive
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

      {/* Tab Panels */}
      {tab === "food" && activePlan && (
        <div role="tabpanel" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl bg-hb-lowBg/60 border border-hb-lowBorder p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold uppercase tracking-wider text-hb-lowInk inline-flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
                  {t.eat_more || "Eat more"}
                </span>
                <span className="text-xs font-bold text-hb-lowInk tabular-nums">
                  {activePlan.eat_more.length}
                </span>
              </div>
              <ul className="space-y-2 text-sm text-hb-ink">
                {activePlan.eat_more.map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-hb-lowInk shrink-0 mt-0.5" aria-hidden="true" />
                    <span className="leading-snug">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-xl bg-hb-highBg/60 border border-hb-highBorder p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold uppercase tracking-wider text-hb-highInk inline-flex items-center gap-1.5">
                  <Ban className="w-4 h-4" aria-hidden="true" />
                  {t.avoid || "Avoid"}
                </span>
                <span className="text-xs font-bold text-hb-highInk tabular-nums">
                  {activePlan.avoid.length}
                </span>
              </div>
              <ul className="space-y-2 text-sm text-hb-ink">
                {activePlan.avoid.map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <Ban className="w-4 h-4 text-hb-highInk shrink-0 mt-0.5" aria-hidden="true" />
                    <span className="leading-snug">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Searchable Indian Food Checker from Knowledge Base */}
          {kbFoods.length > 0 && (
            <div className="rounded-xl bg-hb-subtle/70 border border-hb-border p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-hb-ink">
                    Indian Food Guide ({kbFoods.length} foods — tailored for {activeCondition}: {activeTier} risk)
                  </h3>
                  <p className="text-[11px] text-hb-muted">
                    Sorted for your {activeCondition} lab result ({activeTier} tier) — search English or Hindi names
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex gap-1">
                    {(
                      [
                        ["all", "All"],
                        ["ok", "OK for me"],
                        ["avoid", "Limit / Avoid"],
                      ] as const
                    ).map(([fk, flbl]) => (
                      <button
                        key={fk}
                        type="button"
                        onClick={() => setFoodFilter(fk)}
                        className={`px-2.5 py-1 rounded-full text-[11px] font-bold border transition-colors ${
                          foodFilter === fk
                            ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                            : "bg-hb-surface text-hb-muted border-hb-border hover:text-hb-ink"
                        }`}
                      >
                        {flbl}
                      </button>
                    ))}
                  </div>
                  <div className="relative min-w-[200px] flex-1 max-w-xs">
                    <Search className="w-3.5 h-3.5 text-hb-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                      type="search"
                      value={foodQuery}
                      onChange={(e) => setFoodQuery(e.target.value)}
                      placeholder="Search rice, roti, dal, fruit..."
                      aria-label="Search Indian food guide"
                      className="w-full min-h-[36px] pl-8 pr-3 py-1 rounded-full bg-hb-surface border border-hb-border text-xs text-hb-ink focus:outline-none focus:ring-2 focus:ring-hb-accent"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-64 overflow-y-auto pr-1">
                {kbFoods
                  .filter((f: any) => {
                    const condKey = activeCondition === "metabolic" ? "diabetes" : activeCondition;
                    const code: string = f.codes?.[condKey] || f.advice || "watch";
                    if (foodFilter === "ok" && code !== "ok" && code !== "eat_more") return false;
                    if (foodFilter === "avoid" && code !== "avoid" && code !== "limit" && code !== "ask_dietitian") return false;
                    const q = foodQuery.trim().toLowerCase();
                    if (!q) return true;
                    return (
                      (f.name || "").toLowerCase().includes(q) ||
                      (f.hindi || "").toLowerCase().includes(q) ||
                      (f.group || "").toLowerCase().includes(q) ||
                      (f.note || "").toLowerCase().includes(q)
                    );
                  })
                  .sort((a: any, b: any) => {
                    const condKey = activeCondition === "metabolic" ? "diabetes" : activeCondition;
                    const order: Record<string, number> = { ok: 0, eat_more: 0, watch: 1, moderate: 1, ask_dietitian: 2, limit: 3, avoid: 4 };
                    const ca = a.codes?.[condKey] || a.advice || "watch";
                    const cb = b.codes?.[condKey] || b.advice || "watch";
                    return (order[ca] ?? 2) - (order[cb] ?? 2);
                  })
                  .slice(0, 18)
                  .map((f: any) => {
                    const condKey = activeCondition === "metabolic" ? "diabetes" : activeCondition;
                    const code: string = f.codes?.[condKey] || f.advice || "watch";
                    const badgeClass =
                      code === "ok" || code === "eat_more"
                        ? "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder"
                        : code === "avoid" || code === "limit"
                        ? "bg-hb-highBg text-hb-highInk border-hb-highBorder"
                        : "bg-hb-modBg text-hb-modInk border-hb-modBorder";
                    return (
                      <div
                        key={f.id}
                        className="rounded-xl bg-hb-surface border border-hb-border p-3 space-y-1"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <div className="text-xs font-extrabold text-hb-ink truncate">{f.name}</div>
                            <div className="text-[11px] text-hb-muted truncate">{f.hindi}</div>
                          </div>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase border shrink-0 ${badgeClass}`}
                          >
                            {code.replace("_", " ")}
                          </span>
                        </div>
                        <p className="text-[11px] text-hb-muted leading-snug">{f.note}</p>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "exercise" && activePlan && (
        <div role="tabpanel" className="space-y-4">
          {activePlan.exercise_target.toLowerCase().includes("medical clearance") && (
            <div className="p-3.5 rounded-xl bg-hb-highBg border border-hb-highBorder text-hb-highInk text-xs font-bold flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
              <span>{activePlan.exercise_target}</span>
            </div>
          )}

          <div className="p-3.5 rounded-xl bg-hb-subtle border border-hb-border flex items-center gap-3">
            <Activity className="w-5 h-5 text-hb-accent shrink-0" aria-hidden="true" />
            <div className="text-sm font-bold text-hb-ink">
              <span className="text-[11px] uppercase tracking-wider text-hb-muted block">
                Recommended Target
              </span>
              {activePlan.exercise_target}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activePlan.exercise.map((ex, idx) => (
              <div
                key={ex}
                className="rounded-xl bg-hb-subtle border border-hb-border p-3.5 flex items-start gap-3"
              >
                <span className="w-6 h-6 rounded-full bg-hb-accentSoft text-hb-accentInk text-xs font-extrabold flex items-center justify-center shrink-0 mt-0.5 tabular-nums">
                  {idx + 1}
                </span>
                <p className="text-sm text-hb-ink leading-snug">{ex}</p>
              </div>
            ))}
          </div>

          {kbExercises.length > 0 && (
            <div className="rounded-xl bg-hb-subtle/70 border border-hb-border p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-hb-ink">
                    Exercise &amp; Yoga Library ({kbExercises.length} routines)
                  </h3>
                  <p className="text-[11px] text-hb-muted">
                    Search aerobic, yoga, strength, or rehab routines with safety cautions
                  </p>
                </div>
                <div className="relative min-w-[220px] flex-1 max-w-xs">
                  <Search className="w-3.5 h-3.5 text-hb-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="search"
                    value={exerciseQuery}
                    onChange={(e) => setExerciseQuery(e.target.value)}
                    placeholder="Search walking, yoga, pranayama..."
                    aria-label="Search exercise library"
                    className="w-full min-h-[36px] pl-8 pr-3 py-1 rounded-full bg-hb-surface border border-hb-border text-xs text-hb-ink focus:outline-none focus:ring-2 focus:ring-hb-accent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-64 overflow-y-auto pr-1">
                {kbExercises
                  .filter((ex: any) => {
                    const condKey = activeCondition === "metabolic" ? "diabetes" : activeCondition;
                    const matchesCond =
                      !ex.conditions_safe?.length || ex.conditions_safe.includes(condKey);
                    const q = exerciseQuery.trim().toLowerCase();
                    if (!q) return matchesCond;
                    return (
                      (ex.name || "").toLowerCase().includes(q) ||
                      (ex.hindi || "").toLowerCase().includes(q) ||
                      (ex.category || "").toLowerCase().includes(q) ||
                      (ex.benefits || "").toLowerCase().includes(q)
                    );
                  })
                  .sort((a: any, b: any) => {
                    // When lab report risk is high, prioritize low-intensity & no-clearance-required routines first
                    if (activeTier === "high") {
                      const ca = a.medical_clearance_required ? 1 : 0;
                      const cb = b.medical_clearance_required ? 1 : 0;
                      if (ca !== cb) return ca - cb;
                    }
                    return 0;
                  })
                  .slice(0, 15)
                  .map((ex: any) => (
                    <div
                      key={ex.id}
                      className="rounded-xl bg-hb-surface border border-hb-border p-3 space-y-1"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="text-xs font-extrabold text-hb-ink truncate">{ex.name}</div>
                          <div className="text-[11px] text-hb-muted truncate">{ex.hindi} · {ex.duration_or_reps}</div>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase border shrink-0 ${
                            ex.medical_clearance_required
                              ? "bg-hb-highBg text-hb-highInk border-hb-highBorder"
                              : "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder"
                          }`}
                        >
                          {ex.intensity}
                        </span>
                      </div>
                      <p className="text-[11px] text-hb-ink leading-snug">{ex.benefits}</p>
                      <p className="text-[10px] text-hb-muted leading-snug">{ex.cautions}</p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "tests" && (
        <div role="tabpanel" className="space-y-4">
          {matchedKbGuide ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl bg-hb-subtle border border-hb-border p-4 space-y-2.5">
                <div className="text-xs font-extrabold uppercase tracking-wider text-hb-ink flex items-center gap-1.5">
                  <Stethoscope className="w-4 h-4 text-hb-accentInk" aria-hidden="true" />
                  <span>Recommended Doctor Evaluation &amp; Lab Tests</span>
                </div>
                <ul className="space-y-2 text-sm text-hb-ink">
                  {(matchedKbGuide.doctor_tests || []).map((item: string) => (
                    <li key={item} className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-hb-lowInk shrink-0 mt-0.5" aria-hidden="true" />
                      <span className="leading-snug">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl bg-hb-subtle border border-hb-border p-4 space-y-2.5">
                <div className="text-xs font-extrabold uppercase tracking-wider text-hb-ink flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-hb-accentInk" aria-hidden="true" />
                  <span>Clinical &amp; Hospital Guidance ({matchedKbGuide.tier} tier)</span>
                </div>
                <p className="text-sm text-hb-ink leading-relaxed">
                  {matchedKbGuide.hospital_guidance}
                </p>
                <div className="text-xs font-bold text-hb-muted pt-1">
                  Suggested follow-up: every {matchedKbGuide.followup_days} days
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-hb-muted">
              Clinical test guidance will appear once Knowledge Base data loads.
            </p>
          )}

          {matchedFaqs.length > 0 && (
            <div className="space-y-2.5 pt-2">
              <div className="text-xs font-extrabold uppercase tracking-wider text-hb-muted">
                Deep Clinical Guidance FAQs
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {matchedFaqs.slice(0, 4).map((faq: any) => (
                  <div
                    key={faq.id}
                    className="rounded-xl bg-hb-subtle/70 border border-hb-border p-3.5 space-y-1.5"
                  >
                    <div className="text-xs font-extrabold text-hb-ink">{faq.title}</div>
                    <p className="text-xs text-hb-muted leading-relaxed">{faq.answer}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "followup" && (
        <div role="tabpanel">
          <FollowUpList
            followups={followups}
            lang={lang}
            t={t}
            onDownloadPdf={onDownloadPdf}
            compact
          />
        </div>
      )}

      {activePlan && (
        <div className="pt-3 border-t border-hb-border text-xs text-hb-muted flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            <span>
              <strong>{t.based_on}:</strong> {activePlan.source}
            </span>
            <span>
              <strong>{t.reviewed_by}:</strong> {activePlan.reviewer}
            </span>
          </div>
          <button
            type="button"
            onClick={onSeeFullPlan}
            className="text-xs font-bold text-hb-accentInk hover:underline inline-flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-hb-accent rounded"
          >
            <span>{t.see_full_plan || "See full plan"}</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      )}
    </section>
  );
}
