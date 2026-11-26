"use client";

import React from "react";

interface RiskGaugeProps {
  probability: number | null;
  riskLevel: "Low" | "Moderate" | "High" | string;
}

export function RiskGauge({ probability, riskLevel }: RiskGaugeProps) {
  const pct = probability != null ? Math.max(0, Math.min(100, probability * 100)) : 0;
  const radius = 84;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  const color =
    riskLevel === "Low"
      ? "#10b981"
      : riskLevel === "Moderate"
      ? "#f59e0b"
      : "#ef4444";

  const bgPill =
    riskLevel === "Low"
      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
      : riskLevel === "Moderate"
      ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
      : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300";

  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
      <svg viewBox="0 0 220 130" className="w-56 h-36 overflow-visible">
        <path
          d="M 26 110 A 84 84 0 0 1 194 110"
          fill="none"
          stroke="currentColor"
          className="text-slate-200 dark:text-slate-700"
          strokeWidth="16"
          strokeLinecap="round"
        />
        <path
          d="M 26 110 A 84 84 0 0 1 194 110"
          fill="none"
          stroke={color}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: "stroke-dashoffset 0.7s ease, stroke 0.4s ease" }}
        />
        <text
          x="110"
          y="92"
          textAnchor="middle"
          className="fill-slate-900 dark:fill-white font-extrabold"
          style={{ fontSize: "28px" }}
        >
          {probability != null ? `${pct.toFixed(1)}%` : "N/A"}
        </text>
        <text
          x="110"
          y="114"
          textAnchor="middle"
          className="fill-slate-500 dark:fill-slate-400 font-semibold uppercase"
          style={{ fontSize: "10px", letterSpacing: "0.08em" }}
        >
          Calibrated Risk
        </text>
      </svg>
      <span className={`mt-1 px-3 py-1 rounded-full text-xs font-extrabold ${bgPill}`}>
        {riskLevel} Risk Tier
      </span>
    </div>
  );
}

