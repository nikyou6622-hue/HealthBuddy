"use client";

import React, { useState } from "react";
import { AlertCircle, CheckCircle2, MapPin, Search } from "lucide-react";

interface HospitalListProps {
  hospitals: any[];
  allHospitals?: any[];
  specialistTypes: string[];
  urgency?: string;
  defaultShowAll?: boolean;
  t: Record<string, string>;
  onOpenMap: (hospital: any) => void;
}

export function HospitalList({
  hospitals,
  allHospitals = [],
  specialistTypes,
  urgency,
  defaultShowAll = false,
  t,
  onOpenMap,
}: HospitalListProps) {
  const [sector, setSector] = useState<"all" | "government" | "private" | "emergency">("all");
  const [scope, setScope] = useState<"matched" | "all_verified">("matched");
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(defaultShowAll);

  const sourceList =
    scope === "all_verified" && allHospitals.length > 0 ? allHospitals : hospitals;

  const filtered = sourceList.filter((h) => {
    if (sector === "emergency") {
      if (!h.emergency_24x7) return false;
    } else if (sector !== "all") {
      const notes = `${h.insurance_notes || ""} ${h.name || ""}`.toLowerCase();
      const isGovt =
        notes.includes("public") ||
        notes.includes("cghs") ||
        notes.includes("aiims") ||
        notes.includes("pgimer") ||
        notes.includes("jipmer") ||
        notes.includes("safdarjung") ||
        notes.includes("kem") ||
        notes.includes("nims") ||
        notes.includes("sskm") ||
        notes.includes("rims") ||
        notes.includes("skims");
      if (sector === "government" && !isGovt) return false;
      if (sector === "private" && isGovt) return false;
    }

    const q = query.trim().toLowerCase();
    if (!q) return true;
    return (
      (h.name || "").toLowerCase().includes(q) ||
      (h.city || "").toLowerCase().includes(q) ||
      (h.pincode || "").toLowerCase().includes(q) ||
      (h.insurance_notes || "").toLowerCase().includes(q)
    );
  });

  const visibleHospitals = showAll || query.trim() ? filtered : filtered.slice(0, 10);

  return (
    <div className="rounded-lg bg-hb-surface border border-hb-border p-5 shadow-sm flex flex-col justify-between gap-4">
      <div className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-hb-muted">
              {specialistTypes.length > 0 ? `See a ${specialistTypes.join(" / ")}` : "Specialist care"}
            </span>
            <h3 className="text-base font-extrabold text-hb-ink mt-0.5">
              {t.recommended_care_title || "Recommended care options"} ({filtered.length})
            </h3>
          </div>
          {urgency && (
            <span className="px-2.5 py-1 rounded-full bg-hb-modBg text-hb-modInk border border-hb-modBorder text-[11px] font-bold uppercase">
              {urgency.replace(/_/g, " ")}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 text-hb-muted absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by city, hospital, or scheme..."
              aria-label="Filter hospitals"
              className="w-full min-h-[38px] pl-8 pr-3 py-1 rounded-full bg-hb-subtle border border-hb-border text-xs text-hb-ink focus:outline-none focus:ring-2 focus:ring-hb-accent"
            />
          </div>

          {allHospitals.length > hospitals.length && (
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => setScope("matched")}
                className={`min-h-[38px] px-3 py-1 rounded-full text-xs font-bold border transition-colors ${
                  scope === "matched"
                    ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                    : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
                }`}
              >
                Matched ({hospitals.length})
              </button>
              <button
                type="button"
                onClick={() => setScope("all_verified")}
                className={`min-h-[38px] px-3 py-1 rounded-full text-xs font-bold border transition-colors ${
                  scope === "all_verified"
                    ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                    : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
                }`}
              >
                All Verified ({allHospitals.length})
              </button>
            </div>
          )}
        </div>

        <div className="flex flex-nowrap overflow-x-auto no-scrollbar sm:flex-wrap gap-1.5 pb-1 sm:pb-0" role="group" aria-label="Filter hospital sector">
          {(
            [
              ["all", t.filter_all || "All"],
              ["government", t.filter_govt || "Government / Public"],
              ["private", t.filter_private || "Private / Non-Profit"],
              ["emergency", "24x7 Emergency"],
            ] as const
          ).map(([k, lbl]) => (
            <button
              key={k}
              type="button"
              onClick={() => setSector(k)}
              aria-pressed={sector === k}
              className={`min-h-[36px] px-3.5 py-1 rounded-full text-xs font-bold border focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                sector === k
                  ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                  : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
              }`}
            >
              {lbl}
            </button>
          ))}
        </div>

        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {visibleHospitals.map((h) => (
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
                  {h.phone ? ` • ${h.phone}` : ""}
                </div>
                {h.insurance_notes && (
                  <div className="text-[11px] text-hb-muted">
                    Schemes: <span className="font-semibold text-hb-ink">{h.insurance_notes}</span>
                    {h.teleconsult ? " • Teleconsult available" : ""}
                  </div>
                )}
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
          {visibleHospitals.length === 0 && (
            <p className="text-xs text-hb-muted">No verified hospitals matched the selected filter.</p>
          )}
        </div>

        {filtered.length > 10 && !query.trim() && (
          <button
            type="button"
            onClick={() => setShowAll((v) => !v)}
            className="w-full min-h-[38px] px-4 py-1.5 rounded-full bg-hb-subtle hover:bg-hb-border/50 border border-hb-border text-xs font-bold text-hb-ink transition-colors"
          >
            {showAll ? "Show fewer hospitals" : `Show all ${filtered.length} hospitals`}
          </button>
        )}
      </div>

      <p className="pt-3 border-t border-hb-border text-xs text-hb-muted">
        {t.care_disclaimer || "Matching options, not an endorsement or medical advice."}
      </p>
    </div>
  );
}
