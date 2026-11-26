"use client";

import React, { useMemo, useState } from "react";
import { AlertTriangle, BookOpen, CheckCircle2, HeartPulse, Info, Stethoscope } from "lucide-react";
import { ConditionCardData } from "@/components/Results/ConditionCard";
import { KpiCard } from "@/components/Dashboard/KpiCard";

export interface RiskModuleKb {
  id: string;
  condition_key: string;
  title: string;
  methodology: string;
  why_it_matters: string;
  thresholds: {
    low?: string;
    moderate?: string;
    high?: string;
    skipped?: string;
  };
  modifiable_drivers: string[];
  recommended_tests: string[];
  red_flags: string[];
}

interface RiskGridProps {
  cards: ConditionCardData[];
  t: Record<string, string>;
  loading?: boolean;
  deltas?: Record<string, string>;
  riskKnowledge?: RiskModuleKb[];
  onViewPlan: (conditionKey: string) => void;
  onAddLabs: () => void;
}

const PRIORITY_ORDER: Record<string, number> = {
  high: 0,
  moderate: 1,
  low: 2,
  skipped: 3,
  needs_more_info: 3,
  not_applicable: 4,
};

export function RiskGrid({
  cards,
  t,
  loading = false,
  deltas = {},
  riskKnowledge = [],
  onViewPlan,
  onAddLabs,
}: RiskGridProps) {
  const [filter, setFilter] = useState<"all" | "attention" | "computed" | "skipped">("all");
  const [selectedKbId, setSelectedKbId] = useState<string>("heart_who_cvd");

  const sortedCards = useMemo(() => {
    return [...cards].sort((a, b) => {
      const pa = PRIORITY_ORDER[a.category] ?? 3;
      const pb = PRIORITY_ORDER[b.category] ?? 3;
      return pa - pb;
    });
  }, [cards]);

  const attentionCards = sortedCards.filter((c) => c.category === "high" || c.category === "moderate");
  const computedCards = sortedCards.filter((c) => c.status === "computed");
  const skippedCards = sortedCards.filter((c) => c.status !== "computed");

  const visibleCards =
    filter === "attention"
      ? attentionCards
      : filter === "computed"
      ? computedCards
      : filter === "skipped"
      ? skippedCards
      : sortedCards;

  const activeKb =
    riskKnowledge.find((r) => r.id === selectedKbId) || riskKnowledge[0] || null;

  return (
    <section id="sec-risk" className="scroll-mt-24 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-md bg-hb-accentSoft text-hb-accentInk flex items-center justify-center shrink-0">
            <HeartPulse className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-hb-ink">
              {t.risk_breakdown_title || "Risk & Biomarker Breakdown"}
            </h2>
            <p className="text-xs text-hb-muted">
              {t.risk_urgent_first || "Sorted with urgent and elevated items first"}
            </p>
          </div>
        </div>

        <div className="flex flex-nowrap overflow-x-auto no-scrollbar sm:flex-wrap gap-1.5 pb-1 sm:pb-0 w-full sm:w-auto" role="group" aria-label="Filter risk modules">
          {(
            [
              ["all", t.filter_all || "All", sortedCards.length],
              ["attention", t.filter_needs_review || "Needs review", attentionCards.length],
              ["computed", t.filter_computed || "Computed", computedCards.length],
              ["skipped", t.filter_missing_labs || "Missing labs", skippedCards.length],
            ] as const
          ).map(([key, lbl, count]) => (
            <button
              key={key}
              type="button"
              onClick={() => setFilter(key)}
              aria-pressed={filter === key}
              className={`min-h-[38px] px-3 py-1.5 rounded-full text-xs font-bold border inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                filter === key
                  ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                  : "bg-hb-surface text-hb-muted border-hb-border hover:bg-hb-subtle"
              }`}
            >
              <span>{lbl}</span>
              <span className="tabular-nums text-[11px] opacity-80">({count})</span>
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" aria-busy="true">
          {[1, 2, 3, 4].map((n) => (
            <div
              key={n}
              className="h-40 rounded-lg bg-hb-surface border border-hb-border p-4 animate-pulse space-y-3"
            >
              <div className="h-4 w-2/3 bg-hb-subtle rounded" />
              <div className="h-7 w-1/3 bg-hb-subtle rounded" />
              <div className="h-2 w-full bg-hb-subtle rounded" />
            </div>
          ))}
        </div>
      ) : visibleCards.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {visibleCards.map((card) => (
            <KpiCard
              key={card.id}
              card={card}
              t={t}
              delta={deltas[card.id] || null}
              onViewPlan={onViewPlan}
              onAddLabs={onAddLabs}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-lg bg-hb-surface border border-hb-border p-6 text-center text-sm text-hb-muted">
          No risk modules match this filter.
        </div>
      )}

      {/* Deep Risk Knowledge Base Panel */}
      {activeKb && (
        <div className="rounded-2xl bg-hb-surface border border-hb-border shadow-sm p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-hb-accentInk shrink-0" aria-hidden="true" />
              <h3 className="text-sm font-extrabold text-hb-ink">
                Clinical Risk Knowledge Base — How Each Score Works
              </h3>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {riskKnowledge.map((rk) => (
                <button
                  key={rk.id}
                  type="button"
                  onClick={() => setSelectedKbId(rk.id)}
                  className={`px-3 py-1 rounded-full text-xs font-bold border transition-colors ${
                    activeKb.id === rk.id
                      ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                      : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
                  }`}
                >
                  {rk.title.split("(")[0].trim()}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-7 space-y-3">
              <div>
                <div className="text-xs font-extrabold uppercase tracking-wider text-hb-muted">
                  {activeKb.title}
                </div>
                <p className="text-sm text-hb-ink mt-1 leading-relaxed">{activeKb.methodology}</p>
              </div>
              <div className="p-3 rounded-xl bg-hb-subtle border border-hb-border flex items-start gap-2.5">
                <Info className="w-4 h-4 text-hb-accentInk shrink-0 mt-0.5" aria-hidden="true" />
                <div className="text-xs text-hb-ink leading-relaxed">
                  <strong className="font-bold">Why it matters (South Asian context): </strong>
                  {activeKb.why_it_matters}
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {activeKb.thresholds.low && (
                  <div className="p-2.5 rounded-xl bg-hb-lowBg/60 border border-hb-lowBorder text-hb-lowInk">
                    <strong>Low:</strong> {activeKb.thresholds.low}
                  </div>
                )}
                {activeKb.thresholds.moderate && (
                  <div className="p-2.5 rounded-xl bg-hb-modBg/60 border border-hb-modBorder text-hb-modInk">
                    <strong>Moderate:</strong> {activeKb.thresholds.moderate}
                  </div>
                )}
                {activeKb.thresholds.high && (
                  <div className="p-2.5 rounded-xl bg-hb-highBg/60 border border-hb-highBorder text-hb-highInk">
                    <strong>High:</strong> {activeKb.thresholds.high}
                  </div>
                )}
                {activeKb.thresholds.skipped && (
                  <div className="p-2.5 rounded-xl bg-hb-skipBg border border-hb-skipBorder text-hb-skipInk">
                    <strong>Skipped:</strong> {activeKb.thresholds.skipped}
                  </div>
                )}
              </div>
            </div>

            <div className="lg:col-span-5 space-y-3">
              <div className="p-3.5 rounded-xl bg-hb-subtle border border-hb-border space-y-2">
                <div className="text-xs font-extrabold text-hb-ink flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-hb-lowInk" aria-hidden="true" />
                  <span>Key Modifiable Drivers</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {activeKb.modifiable_drivers.map((d) => (
                    <span
                      key={d}
                      className="px-2.5 py-0.5 rounded-full bg-hb-surface border border-hb-border text-[11px] font-semibold text-hb-ink"
                    >
                      {d}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-hb-subtle border border-hb-border space-y-1.5">
                <div className="text-xs font-extrabold text-hb-ink flex items-center gap-1.5">
                  <Stethoscope className="w-3.5 h-3.5 text-hb-accentInk" aria-hidden="true" />
                  <span>Confirmatory Tests</span>
                </div>
                <ul className="text-xs text-hb-ink space-y-1 list-disc list-inside">
                  {activeKb.recommended_tests.map((tst) => (
                    <li key={tst}>{tst}</li>
                  ))}
                </ul>
              </div>

              {activeKb.red_flags.length > 0 && (
                <div className="p-3 rounded-xl bg-hb-highBg/60 border border-hb-highBorder text-xs text-hb-highInk space-y-1">
                  <div className="font-extrabold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                    <span>Emergency Red Flags</span>
                  </div>
                  <p className="leading-snug">{activeKb.red_flags.join(" • ")}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
