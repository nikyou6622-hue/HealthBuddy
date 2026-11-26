"use client";

import React from "react";
import { TrendingUp } from "lucide-react";

export interface TrendPoint {
  dateLabel: string;
  systolicBp?: number | null;
  bmi?: number | null;
  hba1c?: number | null;
}

interface TrendsChartProps {
  points: TrendPoint[];
  t: Record<string, string>;
  onStartAssess?: () => void;
}

function buildPolyline(values: number[], width: number, height: number): string {
  if (values.length < 2) return "";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values
    .map((v, idx) => {
      const x = (idx / (values.length - 1)) * width;
      const y = height - ((v - min) / span) * (height - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function TrendsChart({ points, t, onStartAssess }: TrendsChartProps) {
  const bpValues = points.map((p) => p.systolicBp).filter((v): v is number => typeof v === "number");
  const bmiValues = points.map((p) => p.bmi).filter((v): v is number => typeof v === "number");

  return (
    <section
      aria-label={t.trends_title || "Health Trends"}
      className="rounded-lg bg-hb-surface border border-hb-border shadow-sm p-5 flex flex-col justify-between gap-4"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-hb-accent shrink-0" aria-hidden="true" />
            <h2 className="text-base font-extrabold text-hb-ink">
              {t.trends_title || "Health Trends"}
            </h2>
          </div>
          <p className="text-xs text-hb-muted mt-0.5">
            {t.trends_sub || "Longitudinal biomarkers from your saved assessments"}
          </p>
        </div>
      </div>

      {points.length >= 2 && (bpValues.length >= 2 || bmiValues.length >= 2) ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 tabular-nums">
          {bpValues.length >= 2 && (
            <div className="rounded-md bg-hb-subtle border border-hb-border p-3 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-hb-ink">Systolic BP</span>
                <span className="font-extrabold text-hb-ink">{bpValues[bpValues.length - 1]} mmHg</span>
              </div>
              <svg viewBox="0 0 180 48" className="w-full h-12 overflow-visible" aria-hidden="true">
                <polyline
                  fill="none"
                  stroke="var(--hb-accent)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={buildPolyline(bpValues, 180, 48)}
                />
              </svg>
              <div className="flex justify-between text-[11px] text-hb-muted">
                <span>{points[0]?.dateLabel}</span>
                <span>{points[points.length - 1]?.dateLabel}</span>
              </div>
            </div>
          )}

          {bmiValues.length >= 2 && (
            <div className="rounded-md bg-hb-subtle border border-hb-border p-3 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-hb-ink">Indian BMI</span>
                <span className="font-extrabold text-hb-ink">{bmiValues[bmiValues.length - 1].toFixed(1)} kg/m²</span>
              </div>
              <svg viewBox="0 0 180 48" className="w-full h-12 overflow-visible" aria-hidden="true">
                <polyline
                  fill="none"
                  stroke="var(--hb-low-ink)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={buildPolyline(bmiValues, 180, 48)}
                />
              </svg>
              <div className="flex justify-between text-[11px] text-hb-muted">
                <span>{points[0]?.dateLabel}</span>
                <span>{points[points.length - 1]?.dateLabel}</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-md bg-hb-subtle border border-hb-border p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <p className="text-xs text-hb-muted leading-relaxed">
            {t.trends_empty || "Complete 2 or more saved assessments to view biomarker trends over time."}
          </p>
          {onStartAssess && (
            <button
              type="button"
              onClick={onStartAssess}
              className="min-h-[38px] px-3 py-1.5 rounded-md bg-hb-surface border border-hb-border text-xs font-bold text-hb-ink hover:bg-hb-border/40 shrink-0"
            >
              {t.nav_new_assessment || "New assessment"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

