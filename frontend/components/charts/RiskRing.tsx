"use client";

import React from "react";
import { Check } from "lucide-react";

interface RiskRingProps {
  completed: number;
  total: number;
  label: string;
}

export function RiskRing({ completed, total, label }: RiskRingProps) {
  const safeTotal = Math.max(total, 1);
  const ratio = Math.max(0, Math.min(1, completed / safeTotal));
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - ratio);

  return (
    <div
      role="img"
      aria-label={`${completed} of ${total} ${label}`}
      className="relative w-28 h-28 shrink-0 flex items-center justify-center"
    >
      <svg viewBox="0 0 112 112" className="w-full h-full -rotate-90" aria-hidden="true">
        <circle
          cx="56"
          cy="56"
          r={radius}
          fill="var(--hb-subtle)"
          stroke="var(--hb-border)"
          strokeWidth="10"
        />
        <circle
          cx="56"
          cy="56"
          r={radius}
          fill="none"
          stroke="var(--hb-accent)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center tabular-nums">
        <span className="text-xl font-extrabold text-hb-ink leading-none">
          {completed}/{total}
        </span>
        <span className="text-[11px] font-semibold text-hb-muted mt-1 px-2 leading-tight">
          {label}
        </span>
      </div>
      <div
        aria-hidden="true"
        className="absolute -bottom-1 w-6 h-6 rounded-full bg-hb-cta text-hb-ctaInk border border-hb-border flex items-center justify-center shadow-sm"
      >
        <Check className="w-3.5 h-3.5" strokeWidth={3} />
      </div>
    </div>
  );
}
