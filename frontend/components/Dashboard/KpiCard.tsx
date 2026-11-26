"use client";

import React from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  Droplet,
  Heart,
  MinusCircle,
  PlusCircle,
  Scale,
  ShieldCheck,
} from "lucide-react";
import { ConditionCardData } from "@/components/Results/ConditionCard";

interface KpiCardProps {
  card: ConditionCardData;
  t: Record<string, string>;
  delta?: string | null;
  onViewPlan: (conditionKey: string) => void;
  onAddLabs: () => void;
}

const VISUAL_BY_ID: Record<
  string,
  {
    iconBg: string;
    iconColor: string;
    Icon: React.ComponentType<{ className?: string }>;
    waveColor: string;
  }
> = {
  heart: { iconBg: "bg-[#FFE4E6]", iconColor: "text-[#F43F5E]", Icon: Heart, waveColor: "#FDA4AF" },
  diabetes: { iconBg: "bg-[#F3E8FF]", iconColor: "text-[#A855F7]", Icon: Droplet, waveColor: "#D8B4FE" },
  bp: { iconBg: "bg-[#E0F2FE]", iconColor: "text-[#0284C7]", Icon: Activity, waveColor: "#7DD3FC" },
  bmi: { iconBg: "bg-[#FEF3C7]", iconColor: "text-[#D97706]", Icon: Scale, waveColor: "#FCD34D" },
  metabolic: { iconBg: "bg-[#FFEDD5]", iconColor: "text-[#EA580C]", Icon: ShieldCheck, waveColor: "#FDBA74" },
  kidney: { iconBg: "bg-[#CCFBF1]", iconColor: "text-[#0D9488]", Icon: Droplet, waveColor: "#99F6E4" },
};

// Sparkline paths per risk tier
function getSparklinePath(category: string): string {
  if (category === "low") return "M0 22 Q 45 10, 95 20 T 185 14 T 220 18";
  if (category === "moderate") return "M0 20 Q 40 12, 90 22 T 175 10 T 220 16";
  if (category === "high") return "M0 18 Q 50 26, 95 14 T 180 22 T 220 10";
  return "M0 20 L220 20"; // skipped — flat line
}

export function KpiCard({ card, t, delta, onViewPlan, onAddLabs }: KpiCardProps) {
  const isSkipped = card.status === "skipped" || card.status === "needs_more_info";
  const vis = VISUAL_BY_ID[card.id] || VISUAL_BY_ID.heart;
  const CardIcon = vis.Icon;

  const statusConfig =
    isSkipped
      ? {
          badgeClass: "bg-hb-skipBg text-hb-skipInk border-hb-skipBorder",
          Icon: MinusCircle,
          label: t.status_skipped || "Skipped",
        }
      : card.category === "high"
      ? {
          badgeClass: "bg-hb-highBg text-hb-highInk border-hb-highBorder",
          Icon: AlertTriangle,
          label: t.status_high || "Needs Attention",
        }
      : card.category === "moderate"
      ? {
          badgeClass: "bg-hb-modBg text-hb-modInk border-hb-modBorder",
          Icon: AlertCircle,
          label: t.status_moderate || "Moderate Risk",
        }
      : {
          badgeClass: "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder",
          Icon: CheckCircle2,
          label: t.status_low || "Low Risk",
        };

  const StatusIcon = statusConfig.Icon;
  const isDeltaUp = delta ? delta.startsWith("+") : false;
  const isDeltaDown = delta ? delta.startsWith("-") : false;
  const sparklinePath = getSparklinePath(isSkipped ? "skipped" : card.category);

  return (
    <article className="relative overflow-hidden rounded-2xl bg-hb-surface border border-hb-border shadow-sm hover:shadow-md transition-all duration-150 flex flex-col justify-between gap-3 p-4">
      {/* Header: icon + name + chevron */}
      <div className="flex items-start justify-between gap-2 relative z-10">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className={`w-9 h-9 rounded-xl ${vis.iconBg} ${vis.iconColor} flex items-center justify-center shrink-0 shadow-sm`}>
            <CardIcon className="w-[18px] h-[18px]" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h3 className="text-sm font-extrabold text-hb-ink truncate leading-tight">{card.label}</h3>
            <p className="text-[11px] text-hb-muted truncate mt-0.5">{card.method}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={isSkipped ? onAddLabs : () => onViewPlan(card.conditionKey)}
          aria-label={isSkipped ? `Add labs for ${card.label}` : `View plan for ${card.label}`}
          className="w-7 h-7 rounded-full hover:bg-hb-subtle text-hb-muted hover:text-hb-ink flex items-center justify-center shrink-0 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors mt-0.5"
        >
          <ChevronRight className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>

      {/* Value + delta */}
      <div className="flex items-baseline justify-between gap-2 tabular-nums relative z-10">
        <div>
          <span className="text-2xl font-extrabold text-hb-ink tracking-tight">
            {isSkipped ? "—" : card.valueDisplay}
          </span>
          {!isSkipped && card.kindLabel && (
            <span className="ml-1.5 text-xs font-medium text-hb-muted">{card.kindLabel}</span>
          )}
        </div>

        {!isSkipped && delta && (
          <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-hb-muted">
            {isDeltaUp && <ArrowUpRight className="w-3.5 h-3.5 text-hb-modInk" aria-hidden="true" />}
            {isDeltaDown && <ArrowDownRight className="w-3.5 h-3.5 text-hb-lowInk" aria-hidden="true" />}
            <span>{delta}</span>
          </span>
        )}
      </div>

      {/* Status badge + action */}
      <div className="flex items-center justify-between gap-2 relative z-10">
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${statusConfig.badgeClass}`}
        >
          <StatusIcon className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>{statusConfig.label}</span>
        </span>

        {isSkipped && (
          <button
            type="button"
            onClick={onAddLabs}
            className="text-xs font-bold text-hb-accentInk hover:underline inline-flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-hb-accent rounded"
          >
            <PlusCircle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t.add_lab_values || "Add lab values"}</span>
          </button>
        )}
      </div>

      {/* Colored sparkline wave at card bottom */}
      <svg
        viewBox="0 0 220 36"
        preserveAspectRatio="none"
        aria-hidden="true"
        className="absolute bottom-0 left-0 w-full h-7 pointer-events-none"
      >
        <defs>
          <linearGradient id={`wf-${card.id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={vis.waveColor} stopOpacity="0.4" />
            <stop offset="100%" stopColor={vis.waveColor} stopOpacity="0.05" />
          </linearGradient>
        </defs>
        <path
          d={`${sparklinePath} L220 36 L0 36 Z`}
          fill={`url(#wf-${card.id})`}
        />
        <path
          d={sparklinePath}
          fill="none"
          stroke={vis.waveColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </article>
  );
}
