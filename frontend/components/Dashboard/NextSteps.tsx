"use client";

import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";

interface NextStepsProps {
  steps: string[];
  t: Record<string, string>;
  onSeeFullPlan: () => void;
  onRecheck: () => void;
}

export function NextSteps({ steps, t, onSeeFullPlan, onRecheck }: NextStepsProps) {
  const displaySteps = steps.slice(0, 3);

  return (
    <section
      aria-label={t.next_steps_title || "Your Next Steps"}
      className="relative overflow-hidden rounded-2xl bg-hb-surface border border-hb-border shadow-sm p-5 flex flex-col justify-between gap-4"
    >
      {/* Header */}
      <div className="flex items-center gap-2.5 relative z-10">
        <div className="w-8 h-8 rounded-xl bg-hb-accentSoft flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-hb-accentInk" aria-hidden="true" />
        </div>
        <h2 className="text-base font-extrabold text-hb-ink">
          {t.next_steps_title || "Your Next Steps"}
        </h2>
      </div>

      {/* Steps list */}
      <ol className="space-y-3 relative z-10">
        {displaySteps.map((step, idx) => (
          <li key={step} className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-hb-cta text-hb-ctaInk font-extrabold text-xs flex items-center justify-center shrink-0 mt-0.5 tabular-nums shadow-sm">
              {idx + 1}
            </span>
            <span className="text-sm text-hb-ink leading-snug flex-1">{step}</span>
          </li>
        ))}
      </ol>

      {/* CTA */}
      <div className="relative z-10 pt-1 border-t border-hb-border">
        <button
          type="button"
          onClick={onSeeFullPlan}
          className="min-h-[42px] w-full px-4 py-2 rounded-xl bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-sm font-extrabold inline-flex items-center justify-center gap-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors mt-2"
        >
          <span>{t.see_full_plan || "See full plan"}</span>
          <ArrowRight className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>

      {/* Stethoscope watermark */}
      <svg
        viewBox="0 0 120 180"
        fill="none"
        stroke="#FFDE82"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="absolute right-3 top-5 w-20 h-32 opacity-50 pointer-events-none dark:opacity-15"
        aria-hidden="true"
      >
        <path d="M40 20 V50 C40 70 80 70 80 50 V20" />
        <circle cx="40" cy="18" r="4" fill="#FFC83D" />
        <circle cx="80" cy="18" r="4" fill="#FFC83D" />
        <path d="M60 66 V115 C60 145 100 145 100 115" />
        <circle cx="100" cy="115" r="9" fill="none" stroke="#FFC83D" strokeWidth="4" />
        <circle cx="100" cy="115" r="4" fill="#FFC83D" />
      </svg>
    </section>
  );
}
