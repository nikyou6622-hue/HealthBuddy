"use client";

import React from "react";
import { Sparkles } from "lucide-react";

interface MlScreeningCardProps {
  mlSecondary: Record<string, any>;
  mlLoading: string | null;
  mlError?: string | null;
  onRunMl: (diseaseKey: "parkinsons" | "liver_disease", kind: "healthy" | "high_risk") => void;
  t: Record<string, string>;
}

export function MlScreeningCard({
  mlSecondary,
  mlLoading,
  mlError,
  onRunMl,
  t,
}: MlScreeningCardProps) {
  return (
    <section
      id="sec-ml"
      className="scroll-mt-24 rounded-lg bg-hb-surface border border-hb-border shadow-sm p-5 sm:p-6 space-y-4"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-md bg-hb-accentSoft text-hb-accentInk flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-extrabold text-hb-ink">
                {t.ml_secondary_title || "Secondary opinion from ML screening"}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full bg-hb-subtle border border-hb-border text-[11px] font-bold text-hb-muted">
                {t.ml_secondary_badge || "Secondary, non-diagnostic"}
              </span>
            </div>
            <p className="text-xs text-hb-muted mt-0.5">
              {t.ml_secondary_sub ||
                "Separate from rule-based clinical scores. Shown for Parkinson's voice and liver screening."}
            </p>
          </div>
        </div>
      </div>

      {mlError && (
        <div
          role="alert"
          className="rounded-md bg-hb-highBg border border-hb-highBorder p-3 text-xs font-semibold text-hb-highInk"
        >
          {mlError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(
          [
            ["parkinsons", "Parkinson's voice screening (22 biomarkers)"],
            ["liver_disease", "Liver function ML screening (10 biomarkers)"],
          ] as ["parkinsons" | "liver_disease", string][]
        ).map(([dKey, title]) => {
          const res = mlSecondary[dKey];
          const isRunning = mlLoading === dKey;
          const pct = typeof res?.probability === "number" ? Math.round(res.probability * 100) : null;
          const badgeClass =
            res?.risk_level === "High"
              ? "bg-hb-highBg text-hb-highInk border-hb-highBorder"
              : res?.risk_level === "Moderate"
              ? "bg-hb-modBg text-hb-modInk border-hb-modBorder"
              : "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder";

          return (
            <div
              key={dKey}
              className="rounded-md bg-hb-subtle border border-hb-border p-4 space-y-3"
            >
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-bold text-sm text-hb-ink">{title}</h3>
                {isRunning && (
                  <span className="text-xs font-bold text-hb-accentInk animate-pulse">
                    Running...
                  </span>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => onRunMl(dKey, "healthy")}
                  disabled={isRunning}
                  className="min-h-[40px] px-3 py-1.5 rounded-md bg-hb-surface hover:bg-hb-border/40 border border-hb-border text-xs font-bold text-hb-ink focus:outline-none focus:ring-2 focus:ring-hb-accent disabled:opacity-50 transition-colors"
                >
                  Run sample (Healthy)
                </button>
                <button
                  type="button"
                  onClick={() => onRunMl(dKey, "high_risk")}
                  disabled={isRunning}
                  className="min-h-[40px] px-3 py-1.5 rounded-md bg-hb-surface hover:bg-hb-border/40 border border-hb-border text-xs font-bold text-hb-ink focus:outline-none focus:ring-2 focus:ring-hb-accent disabled:opacity-50 transition-colors"
                >
                  Run sample (Elevated)
                </button>
              </div>

              {res && (
                <div className="rounded-md bg-hb-surface border border-hb-border p-3 space-y-2.5 text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full font-bold border ${badgeClass}`}>
                      {res.risk_level} ({res.label})
                    </span>
                    <span className="text-hb-muted font-semibold">
                      Confidence: <strong className="text-hb-ink">{res.confidence_flag}</strong>
                    </span>
                  </div>

                  {pct !== null && (
                    <div className="space-y-1 tabular-nums">
                      <div className="flex justify-between text-[11px] font-semibold text-hb-muted">
                        <span>0%</span>
                        <span className="text-hb-ink font-bold">{pct}% calibrated probability</span>
                        <span>100%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-hb-subtle overflow-hidden">
                        <div
                          className="h-full rounded-full bg-hb-accent transition-all duration-300"
                          style={{ width: `${Math.max(4, Math.min(100, pct))}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

