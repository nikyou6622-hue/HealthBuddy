"use client";

import React, { useState } from "react";
import { AlertCircle, CheckCircle2, MapPin } from "lucide-react";

interface HospitalListProps {
  hospitals: any[];
  specialistTypes: string[];
  urgency?: string;
  t: Record<string, string>;
  onOpenMap: (hospital: any) => void;
}

export function HospitalList({
  hospitals,
  specialistTypes,
  urgency,
  t,
  onOpenMap,
}: HospitalListProps) {
  const [sector, setSector] = useState<"all" | "government" | "private">("all");

  const filtered = hospitals.filter((h) => {
    if (sector === "all") return true;
    const notes = `${h.insurance_notes || ""} ${h.name || ""}`.toLowerCase();
    const isGovt = notes.includes("public") || notes.includes("cghs") || notes.includes("aiims") || notes.includes("pgimer") || notes.includes("jipmer") || notes.includes("safdarjung") || notes.includes("kem");
    return sector === "government" ? isGovt : !isGovt;
  });

  const topThree = filtered.slice(0, 3);

  return (
    <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm flex flex-col justify-between gap-4">
      <div className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B5B2E]">
              {specialistTypes.length > 0 ? `See a ${specialistTypes.join(" / ")}` : "Specialist care"}
            </span>
            <h3 className="text-xl font-extrabold text-[#2B2208] mt-0.5">
              {t.recommended_care_title || "Recommended care options"}
            </h3>
          </div>
          {urgency && (
            <span className="px-2.5 py-1 rounded-full bg-[#FEF3C7] text-[#78350F] border border-[#FDE68A] text-[11px] font-bold uppercase">
              {urgency.replace(/_/g, " ")}
            </span>
          )}
        </div>

        {/* Government / Private Filter */}
        <div className="flex flex-wrap gap-2">
          {(
            [
              ["all", t.filter_all || "All"],
              ["government", t.filter_govt || "Government / Public"],
              ["private", t.filter_private || "Private / Non-Profit"],
            ] as const
          ).map(([k, lbl]) => (
            <button
              key={k}
              type="button"
              onClick={() => setSector(k)}
              className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-xs font-bold border focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
                sector === k
                  ? "bg-[#FFC83D] text-[#2B2208] border-[#FFC83D]"
                  : "bg-[#FFF9E3] text-[#6B5B2E] border-[#EFE4BE]"
              }`}
            >
              {lbl}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          {topThree.map((h) => (
            <div
              key={h.id}
              className="rounded-2xl bg-[#FFF9E3]/70 border border-[#EFE4BE] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-extrabold text-sm text-[#2B2208]">{h.name}</span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#DCFCE7] text-[#14532D] text-[11px] font-bold">
                    <CheckCircle2 className="w-3 h-3" strokeWidth={2.2} />
                    {t.verified_tag || "Verified"}
                  </span>
                  {h.emergency_24x7 && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#FEE2E2] text-[#7F1D1D] text-[11px] font-bold">
                      <AlertCircle className="w-3 h-3" strokeWidth={2.2} />
                      Emergency-capable
                    </span>
                  )}
                </div>
                <div className="text-xs text-[#6B5B2E] tabular-nums">
                  {h.city} ({h.pincode})
                  {h.distance_km != null ? ` • ${h.distance_km} km` : ""}
                </div>
                {h.match_reasons && h.match_reasons.length > 0 && (
                  <div className="text-[11px] text-[#6B5B2E]">{h.match_reasons[0]}</div>
                )}
              </div>

              <button
                type="button"
                onClick={() => onOpenMap(h)}
                className="min-h-[44px] px-3.5 py-2 rounded-xl bg-white hover:bg-[#FFC83D] text-[#2B2208] border border-[#EFE4BE] text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition"
              >
                <MapPin className="w-4 h-4" strokeWidth={2} />
                <span>{t.open_map || "Open map"}</span>
              </button>
            </div>
          ))}
          {topThree.length === 0 && (
            <p className="text-xs text-[#6B5B2E]">No verified hospitals matched the selected filter.</p>
          )}
        </div>
      </div>

      <p className="pt-3 border-t border-[#EFE4BE] text-xs text-[#6B5B2E]">
        {t.care_disclaimer || "Matching options, not an endorsement or medical advice."}
      </p>
    </div>
  );
}
