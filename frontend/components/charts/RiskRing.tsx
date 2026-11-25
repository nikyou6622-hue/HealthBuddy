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
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - ratio);

  return (
    <div
      role="img"
      aria-label={`${completed} of ${total} ${label}`}
      className="relative w-32 h-32 shrink-0 flex items-center justify-center"
    >
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90" aria-hidden="true">
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="rgba(255, 255, 255, 0.45)"
          stroke="rgba(43, 34, 8, 0.12)"
          strokeWidth="11"
        />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="#E59A00"
          strokeWidth="11"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center tabular-nums">
        <span className="text-2xl font-extrabold text-[#2B2208] leading-none">
          {completed}/{total}
        </span>
        <span className="text-[11px] font-bold text-[#6B5B2E] mt-1">
          {label}
        </span>
      </div>
      <div
        aria-hidden="true"
        className="absolute -bottom-1 w-6 h-6 rounded-full bg-[#2B2208] text-[#FFC83D] flex items-center justify-center shadow"
      >
        <Check className="w-3.5 h-3.5" strokeWidth={3} />
      </div>
    </div>
  );
}
