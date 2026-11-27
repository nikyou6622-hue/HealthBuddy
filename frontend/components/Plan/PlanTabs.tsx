"use client";

import React, { useRef, useState } from "react";
import { Calendar, Check, Dumbbell, Stethoscope, Utensils, X } from "lucide-react";
import { LocalizedPlan } from "@/lib/plans";

type PlanTabKey = "doctor" | "exercise" | "food" | "followup";

interface PlanTabsProps {
  plan: LocalizedPlan;
  t: Record<string, string>;
  locale: "en" | "hi";
}

export function PlanTabs({ plan, t, locale }: PlanTabsProps) {
  const [active, setActive] = useState<PlanTabKey>("doctor");
  const tabRefs = useRef<Record<PlanTabKey, HTMLButtonElement | null>>({
    doctor: null,
    exercise: null,
    food: null,
    followup: null,
  });

  const tabs: [PlanTabKey, string, any][] = [
    ["doctor", t.plan_tab_doctor || "Doctor and tests", Stethoscope],
    ["exercise", t.plan_tab_exercise || "Exercise", Dumbbell],
    ["food", t.plan_tab_food || "Food", Utensils],
    ["followup", t.plan_tab_followup || "Follow-up", Calendar],
  ];

  const handleKeyDown = (e: React.KeyboardEvent, idx: number) => {
    let nextIdx = idx;
    if (e.key === "ArrowRight") nextIdx = (idx + 1) % tabs.length;
    else if (e.key === "ArrowLeft") nextIdx = (idx - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") nextIdx = 0;
    else if (e.key === "End") nextIdx = tabs.length - 1;
    else return;

    e.preventDefault();
    const nextKey = tabs[nextIdx][0];
    setActive(nextKey);
    tabRefs.current[nextKey]?.focus();
  };

  const dueDate = new Date(Date.now() + plan.followup_months * 30 * 86400000);
  const formattedDue = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(dueDate);

  return (
    <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm flex flex-col justify-between gap-5">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B5B2E]">
              Care guidance • {plan.tier} tier
            </span>
            <h3 className="text-xl font-extrabold text-[#2B2208] mt-0.5">{plan.title}</h3>
          </div>
          <div className="flex items-center gap-2">
            {plan.is_pending_review && (
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-[#FEF3C7] text-[#78350F] border border-[#FDE68A]">
                {t.pending_review || "Pending doctor review"}
              </span>
            )}
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#FFF9E3] border border-[#EFE4BE] text-[#6B5B2E]">
              v{plan.version}
            </span>
          </div>
        </div>

        <div role="tablist" aria-label="Care plan sections" className="flex flex-wrap gap-2">
          {tabs.map(([k, label, Icon], idx) => (
            <button
              key={k}
              ref={(el) => {
                tabRefs.current[k] = el;
              }}
              role="tab"
              id={`tab-${k}`}
              aria-selected={active === k}
              aria-controls={`panel-${k}`}
              tabIndex={active === k ? 0 : -1}
              onClick={() => setActive(k)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              className={`min-h-[44px] px-3.5 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
                active === k
                  ? "bg-[#FFC83D] text-[#2B2208] shadow-sm"
                  : "bg-[#FFF9E3] text-[#6B5B2E] hover:bg-[#FFC83D]/30 border border-[#EFE4BE]"
              }`}
            >
              <Icon className="w-4 h-4" strokeWidth={2} />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div
          role="tabpanel"
          id={`panel-${active}`}
          aria-labelledby={`tab-${active}`}
          className="text-sm text-[#2B2208] pt-1"
        >
          {active === "doctor" && (
            <ul className="space-y-2.5">
              {plan.doctor_tests.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-[#15803D] shrink-0 mt-0.5" strokeWidth={2.2} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}

          {active === "exercise" && (
            <div className="space-y-3">
              <div className="rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] p-3 text-xs font-bold text-[#2B2208]">
                {plan.exercise_target}
              </div>
              <ul className="space-y-2">
                {plan.exercise.map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-[#15803D] shrink-0 mt-0.5" strokeWidth={2.2} />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {active === "food" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-xl bg-[#DCFCE7]/50 border border-[#BBF7D0] p-3.5 space-y-2">
                <div className="text-xs font-extrabold uppercase tracking-wider text-[#14532D]">
                  {t.eat_more || "Eat more"}
                </div>
                <ul className="space-y-1.5 text-xs text-[#14532D]">
                  {plan.eat_more.map((item) => (
                    <li key={item} className="flex items-start gap-1.5">
                      <Check className="w-3.5 h-3.5 shrink-0 mt-0.5" strokeWidth={2.2} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-xl bg-[#FEE2E2]/50 border border-[#FECACA] p-3.5 space-y-2">
                <div className="text-xs font-extrabold uppercase tracking-wider text-[#7F1D1D]">
                  {t.avoid || "Avoid"}
                </div>
                <ul className="space-y-1.5 text-xs text-[#7F1D1D]">
                  {plan.avoid.map((item) => (
                    <li key={item} className="flex items-start gap-1.5">
                      <X className="w-3.5 h-3.5 shrink-0 mt-0.5" strokeWidth={2.2} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {active === "followup" && (
            <div className="rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] p-4 space-y-1.5 tabular-nums">
              <p className="font-bold">
                Re-screen in {plan.followup_months} months
              </p>
              <p className="text-xs text-[#6B5B2E]">
                Target follow-up date: <strong className="text-[#2B2208]">{formattedDue}</strong>
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="pt-3 border-t border-[#EFE4BE] text-xs text-[#6B5B2E] flex flex-wrap justify-between gap-2">
        <span>
          <strong>{t.based_on || "Based on"}:</strong> {plan.source}
        </span>
        <span>
          <strong>{t.reviewed_by || "Reviewed by"}:</strong> {plan.reviewer}
        </span>
      </div>
    </div>
  );
}
