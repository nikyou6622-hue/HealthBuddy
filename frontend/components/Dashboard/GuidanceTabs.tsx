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
  lang,
  t,
  onSeeFullPlan,
  onDownloadPdf,
}: GuidanceTabsProps) {
  const [tab, setTab] = useState<"food" | "exercise" | "tests" | "followup">("food");

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

        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Select condition">
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
        className="flex flex-wrap items-center gap-4 border-b border-hb-border"
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
