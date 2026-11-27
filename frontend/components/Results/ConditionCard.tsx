"use client";

import React from "react";
import { Activity, ChevronRight, Droplet, Heart, PlusCircle, Scale, ShieldCheck } from "lucide-react";

export interface ConditionCardData {
  id: string;
  conditionKey: string;
  label: string;
  kindLabel: string;
  valueDisplay: string;
  status: "computed" | "skipped" | "needs_more_info";
  category: "low" | "moderate" | "high" | "skipped" | "not_applicable" | "needs_more_info";
  progressPct: number;
  method: string;
  skipReason?: string | null;
  confidenceFlag?: string;
  // Specific visual styles matching the mockup
  theme?: "pink" | "purple" | "orange" | "blue" | "default";
}

interface ConditionCardProps {
  card: ConditionCardData;
  t: Record<string, string>;
  onViewPlan: (conditionKey: string) => void;
  onAddLabs: () => void;
}

export function ConditionCard({ card, t, onViewPlan, onAddLabs }: ConditionCardProps) {
  const isSkipped = card.status === "skipped" || card.status === "needs_more_info";

  // Dedicated visual themes matching mockup:
  // 1. Heart Disease: Pink heart icon, Low Risk green pill, pink wave
  // 2. Prediabetes: Purple droplet, Moderate Risk amber pill, purple wave
  // 3. Diabetes Risk: Red droplet, Needs Attention orange pill, orange wave
  // 4. Blood Pressure: Blue gauge/meter, Normal Range green pill, blue wave
  const themeConfigs: Record<
    string,
    {
      iconBg: string;
      iconColor: string;
      Icon: any;
      chipClass: string;
      waveGradient: [string, string];
      defaultChipLabel: string;
    }
  > = {
    heart: {
      iconBg: "bg-[#FFE4E6]",
      iconColor: "text-[#F43F5E]",
      Icon: Heart,
      chipClass: "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
      waveGradient: ["#FDA4AF", "#FFF1F2"],
      defaultChipLabel: "Low Risk",
    },
    diabetes: {
      iconBg: "bg-[#F3E8FF]",
      iconColor: "text-[#A855F7]",
      Icon: Droplet,
      chipClass: "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]",
      waveGradient: ["#D8B4FE", "#FAF5FF"],
      defaultChipLabel: "Moderate Risk",
    },
    diabetes_risk: {
      iconBg: "bg-[#FEE2E2]",
      iconColor: "text-[#EF4444]",
      Icon: Droplet,
      chipClass: "bg-[#FFEDD5] text-[#C2410C] border-[#FED7AA]",
      waveGradient: ["#FDBA74", "#FFF7ED"],
      defaultChipLabel: "Needs Attention",
    },
    bp: {
      iconBg: "bg-[#E0F2FE]",
      iconColor: "text-[#0284C7]",
      Icon: Activity,
      chipClass: "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]",
      waveGradient: ["#7DD3FC", "#F0F9FF"],
      defaultChipLabel: "Normal Range",
    },
    bmi: {
      iconBg: "bg-[#FEF3C7]",
      iconColor: "text-[#D97706]",
      Icon: Scale,
      chipClass: "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]",
      waveGradient: ["#FCD34D", "#FFFBEB"],
      defaultChipLabel: "Overweight (Indian)",
    },
    metabolic: {
      iconBg: "bg-[#FFEDD5]",
      iconColor: "text-[#EA580C]",
      Icon: ShieldCheck,
      chipClass: "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]",
      waveGradient: ["#FDBA74", "#FFF7ED"],
      defaultChipLabel: "Moderate",
    },
    kidney: {
      iconBg: "bg-[#CCFBF1]",
      iconColor: "text-[#0D9488]",
      Icon: Droplet,
      chipClass: "bg-[#F1F5F9] text-[#475569] border-[#CBD5E1]",
      waveGradient: ["#99F6E4", "#F0FDFA"],
      defaultChipLabel: "Skipped",
    },
  };

  const currentThemeKey =
    card.id === "diabetes" && card.label.toLowerCase().includes("prediabetes")
      ? "diabetes"
      : card.id === "diabetes_risk"
      ? "diabetes_risk"
      : themeConfigs[card.id]
      ? card.id
      : "heart";

  const cfg = themeConfigs[currentThemeKey];
  const IconComp = cfg.Icon;

  // Determine Chip Text & Style
  let chipText = cfg.defaultChipLabel;
  let chipStyle = cfg.chipClass;

  if (isSkipped) {
    chipText = card.status === "needs_more_info" ? "Needs info" : (t.status_skipped || "Skipped");
    chipStyle = "bg-[#F1F5F9] text-[#64748B] border-[#E2E8F0]";
  } else if (card.category === "low") {
    chipText = t.status_low || "Low Risk";
    chipStyle = "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]";
  } else if (card.category === "high") {
    chipText = t.status_high || "Needs Attention";
    chipStyle = "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]";
  } else if (card.category === "moderate") {
    chipText = card.id === "diabetes_risk" ? "Needs Attention" : (t.status_moderate || "Moderate Risk");
    chipStyle = card.id === "diabetes_risk"
      ? "bg-[#FFEDD5] text-[#C2410C] border-[#FED7AA]"
      : "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]";
  }

  const gradId = `wave-grad-${card.id}`;

  return (
    <div
      className={`relative overflow-hidden rounded-[22px] bg-white p-5 shadow-warm flex flex-col justify-between gap-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${
        isSkipped ? "border-2 border-dashed border-[#D6C79A]" : "border border-[#F3EACB]"
      }`}
    >
      {/* Top Header: Icon + Title + Chevron Right */}
      <div className="flex items-center justify-between gap-2 relative z-10">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className={`w-8 h-8 rounded-full ${cfg.iconBg} ${cfg.iconColor} flex items-center justify-center shrink-0 shadow-sm`}>
            <IconComp className="w-4 h-4 fill-current" strokeWidth={1.8} />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-extrabold text-[#2B2208] tracking-tight truncate">
              {card.label}
            </h3>
            <p className="text-[10.5px] font-medium text-[#7C6C3E] truncate">
              {card.kindLabel}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => (isSkipped ? onAddLabs() : onViewPlan(card.conditionKey))}
          aria-label={isSkipped ? `Add lab values for ${card.label}` : `View plan for ${card.label}`}
          className="w-7 h-7 rounded-full flex items-center justify-center text-[#A39263] hover:bg-[#FFF9E3] hover:text-[#2B2208] focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition"
        >
          <ChevronRight className="w-4 h-4" strokeWidth={2.4} />
        </button>
      </div>

      {/* Value + Status Chip */}
      <div className="space-y-2 relative z-10 pt-1">
        <div className="text-[28px] sm:text-[32px] font-black text-[#2B2208] tracking-tight leading-none tabular-nums">
          {isSkipped ? "—" : card.valueDisplay}
        </div>
        <div>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-extrabold border ${chipStyle}`}
          >
            {chipText}
          </span>
        </div>
      </div>

      {/* Bottom Method or Action */}
      <div className="relative z-10 pt-1">
        {isSkipped ? (
          <button
            type="button"
            onClick={onAddLabs}
            className="min-h-[38px] w-full px-3 py-1.5 rounded-xl bg-[#FFF9E3] hover:bg-[#FFC83D]/40 text-[#2B2208] border border-[#EFE4BE] text-xs font-bold inline-flex items-center justify-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>{t.add_lab_values || "Add lab values"}</span>
          </button>
        ) : (
          <p className="text-[10.5px] text-[#8C7A4A] truncate font-medium" title={card.method}>
            {card.method}
          </p>
        )}
      </div>

      {/* Signature Smooth Sparkline Wave at Bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-12 overflow-hidden pointer-events-none rounded-b-[22px]">
        <svg
          viewBox="0 0 300 60"
          preserveAspectRatio="none"
          aria-hidden="true"
          className="w-full h-full opacity-60"
        >
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={cfg.waveGradient[0]} stopOpacity="0.8" />
              <stop offset="100%" stopColor={cfg.waveGradient[1]} stopOpacity="0.1" />
            </linearGradient>
          </defs>
          <path
            d="M0 45 C 50 15, 100 55, 150 35 C 200 15, 250 50, 300 25 L 300 60 L 0 60 Z"
            fill={`url(#${gradId})`}
          />
          <path
            d="M0 45 C 50 15, 100 55, 150 35 C 200 15, 250 50, 300 25"
            fill="none"
            stroke={cfg.waveGradient[0]}
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  );
}
