"use client";

import React from "react";
import { AlertCircle, Calendar, CheckCircle2, RefreshCw } from "lucide-react";
import { RiskRing } from "@/components/charts/RiskRing";

interface SummaryHeaderProps {
  completedCount: number;
  totalCount: number;
  lowCount: number;
  moderateCount: number;
  highCount: number;
  skippedCount: number;
  lastAssessedIso?: string | null;
  lang: "en" | "hi";
  t: Record<string, string>;
  onRecheck: () => void;
}

export function SummaryHeader({
  completedCount,
  totalCount,
  lowCount,
  moderateCount,
  highCount,
  skippedCount,
  lastAssessedIso,
  lang,
  t,
  onRecheck,
}: SummaryHeaderProps) {
  const needsAttention = highCount > 0 || moderateCount > 0;

  let formattedDate = lang === "hi" ? "नमूना स्नैपशॉट" : "Sample snapshot";
  if (lastAssessedIso) {
    const d = new Date(lastAssessedIso);
    if (!Number.isNaN(d.getTime())) {
      formattedDate = new Intl.DateTimeFormat(lang === "hi" ? "hi-IN" : "en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      }).format(d);
    }
  }

  return (
    <section
      aria-label={t.summary_title || "Health Summary"}
      className="relative overflow-hidden rounded-2xl border border-[#F5DC8C] dark:border-hb-border shadow-sm"
      style={{
        background: "linear-gradient(135deg, #FFF5CC 0%, #FFF0A8 35%, #FFE566 70%, #FFD24C 100%)",
      }}
    >
      {/* Top Label */}
      <div className="px-5 pt-4 pb-0">
        <span className="text-[11px] font-extrabold tracking-widest uppercase text-[#8B6914] dark:text-hb-muted">
          {t.health_risk_assessment || "Health Risk Assessment"}
        </span>
      </div>

      <div className="p-4 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 sm:gap-5">
        {/* Left: Title + subtitle + date + pills */}
        <div className="flex-1 min-w-0 relative z-10">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-hb-ink tracking-tight leading-tight mt-1">
            {lang === "hi" ? (
              <>आपका <span className="text-[#C07A00]">स्वास्थ्य</span> स्नैपशॉट</>
            ) : (
              <>Your <span className="text-[#C07A00]">health</span> snapshot</>
            )}
          </h1>
          <p className="text-sm font-medium text-[#5A4010] mt-1.5 max-w-sm">
            {t.hero_snapshot_sub ||
              "A quick overview of your health based on your latest assessment."}
          </p>

          {/* Date + summary badge */}
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#78600A]">
              <Calendar className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
              <span>
                {t.last_assessed || "Last assessed"}:{" "}
                <strong className="text-hb-ink">{formattedDate}</strong>
              </span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/70 dark:bg-hb-surface/50 text-hb-ink text-xs font-extrabold border border-white/80 shadow-sm">
              {needsAttention ? (
                <AlertCircle className="w-3.5 h-3.5 shrink-0 text-orange-600" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-green-600" aria-hidden="true" />
              )}
              <span>{t.summary_title || "Overall Summary"}</span>
            </span>
          </div>

          {/* Status pills */}
          <div className="flex flex-wrap items-center gap-2 mt-2.5 tabular-nums">
            <span className="px-2.5 py-0.5 rounded-full bg-green-100 text-green-800 border border-green-200 text-xs font-bold">
              {t.status_low || "Low"}: {lowCount}
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200 text-xs font-bold">
              {t.status_moderate || "Moderate"}: {moderateCount}
            </span>
            {highCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full bg-red-100 text-red-800 border border-red-200 text-xs font-bold">
                {t.status_high || "High"}: {highCount}
              </span>
            )}
            {skippedCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full bg-hb-skipBg text-hb-skipInk border border-hb-skipBorder text-xs font-bold">
                {t.status_skipped || "Skipped"}: {skippedCount}
              </span>
            )}
          </div>
        </div>

        {/* Center: Risk Ring */}
        <div className="flex items-center justify-center shrink-0 relative z-10">
          <RiskRing
            completed={completedCount}
            total={totalCount}
            label={t.checks_done || "checks done"}
          />
        </div>

        {/* Right: Heart+ECG decoration + Re-check CTA */}
        <div className="shrink-0 flex flex-col items-center md:items-end gap-4 relative z-10">
          <div className="hidden md:block" aria-hidden="true">
            <svg viewBox="0 0 160 110" fill="none" className="w-32 h-20 opacity-85">
              {/* Heart */}
              <path
                d="M80 90 C80 90 44 68 44 46 C44 35 52 27 61 27 C67 27 73 30.5 76 35 C79 30.5 85 27 91 27 C100 27 108 35 108 46 C108 68 80 90 80 90Z"
                fill="#FFC83D"
                opacity="0.75"
                stroke="#C07A00"
                strokeWidth="1.5"
              />
              {/* ECG line */}
              <path
                d="M20 55 L40 55 L48 38 L55 72 L62 48 L68 60 L76 55 L140 55"
                stroke="#2B2208"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.85"
              />
            </svg>
          </div>

          <button
            type="button"
            onClick={onRecheck}
            className="min-h-[44px] w-full sm:w-auto px-5 py-2.5 rounded-full bg-white/90 hover:bg-white text-hb-ink border border-white/80 text-sm font-extrabold inline-flex items-center justify-center gap-2 shadow-md focus:outline-none focus:ring-2 focus:ring-hb-accent focus:ring-offset-2 transition-colors duration-150"
          >
            <RefreshCw className="w-4 h-4" strokeWidth={2.5} aria-hidden="true" />
            <span>{t.btn_recheck || "Re-check my health"}</span>
          </button>
        </div>
      </div>

      {/* Bottom wave */}
      <svg
        viewBox="0 0 1200 60"
        preserveAspectRatio="none"
        aria-hidden="true"
        className="absolute bottom-0 left-0 w-full h-10 opacity-25 pointer-events-none"
      >
        <path d="M0 40 Q 300 10, 600 35 T 1200 20 L 1200 60 L 0 60 Z" fill="#C07A00" />
      </svg>
    </section>
  );
}
