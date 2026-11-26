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
    const isGovt =
      notes.includes("public") ||
      notes.includes("cghs") ||
      notes.includes("aiims") ||
      notes.includes("pgimer") ||
      notes.includes("jipmer") ||
      notes.includes("safdarjung") ||
      notes.includes("kem");
    return sector === "government" ? isGovt : !isGovt;
  });

  const topThree = filtered.slice(0, 3);

  return (
    <div className="rounded-lg bg-hb-surface border border-hb-border p-5 shadow-sm flex flex-col justify-between gap-4">
      <div className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-hb-muted">
              {specialistTypes.length > 0 ? `See a ${specialistTypes.join(" / ")}` : "Specialist care"}
            </span>
            <h3 className="text-base font-extrabold text-hb-ink mt-0.5">
              {t.recommended_care_title || "Recommended care options"}
            </h3>
          </div>
          {urgency && (
            <span className="px-2.5 py-1 rounded-full bg-hb-modBg text-hb-modInk border border-hb-modBorder text-[11px] font-bold uppercase">
              {urgency.replace(/_/g, " ")}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter hospital sector">
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
              aria-pressed={sector === k}
              className={`min-h-[40px] px-3.5 py-1.5 rounded-full text-xs font-bold border focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                sector === k
                  ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                  : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
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
              className="rounded-md bg-hb-subtle border border-hb-border p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-sm text-hb-ink">{h.name}</span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-hb-lowBg text-hb-lowInk border border-hb-lowBorder text-[11px] font-bold">
                    <CheckCircle2 className="w-3 h-3" strokeWidth={2.2} aria-hidden="true" />
                    {t.verified_tag || "Verified"}
                  </span>
                  {h.emergency_24x7 && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-hb-highBg text-hb-highInk border border-hb-highBorder text-[11px] font-bold">
                      <AlertCircle className="w-3 h-3" strokeWidth={2.2} aria-hidden="true" />
                      Emergency-capable
                    </span>
                  )}
                </div>
                <div className="text-xs text-hb-muted tabular-nums">
                  {h.city} ({h.pincode})
                  {h.distance_km != null ? ` • ${h.distance_km} km` : ""}
                </div>
                {h.match_reasons && h.match_reasons.length > 0 && (
                  <div className="text-xs text-hb-muted">{h.match_reasons[0]}</div>
                )}
              </div>

              <button
                type="button"
                onClick={() => onOpenMap(h)}
                className="min-h-[42px] px-3.5 py-2 rounded-md bg-hb-surface hover:bg-hb-cta hover:text-hb-ctaInk text-hb-ink border border-hb-border text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
              >
                <MapPin className="w-4 h-4" strokeWidth={2} aria-hidden="true" />
                <span>{t.open_map || "Open map"}</span>
              </button>
            </div>
          ))}
          {topThree.length === 0 && (
            <p className="text-xs text-hb-muted">No verified hospitals matched the selected filter.</p>
          )}
        </div>
      </div>

      <p className="pt-3 border-t border-hb-border text-xs text-hb-muted">
        {t.care_disclaimer || "Matching options, not an endorsement or medical advice."}
      </p>
    </div>
  );
}
