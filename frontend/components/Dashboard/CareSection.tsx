"use client";

import React from "react";
import { Building2, ShieldCheck, Stethoscope } from "lucide-react";
import { HospitalList } from "@/components/Care/HospitalList";
import { HospitalMap } from "@/components/map/HospitalMap";

interface CareSectionProps {
  hospitals: any[];
  matchedHospitals: any[];
  specialistTypes: string[];
  urgency?: string;
  focusedHospital: any;
  onSelectHospital: (h: any) => void;
  kbDoctors?: any[];
  kbServices?: any[];
  kbCareFaqs?: any[];
  t: Record<string, string>;
}

export function CareSection({
  hospitals,
  matchedHospitals,
  specialistTypes,
  urgency,
  focusedHospital,
  onSelectHospital,
  kbDoctors = [],
  kbServices = [],
  kbCareFaqs = [],
  t,
}: CareSectionProps) {
  const listData = matchedHospitals.length > 0 ? matchedHospitals : hospitals;
  const mapHospitals = focusedHospital
    ? [focusedHospital, ...listData.filter((h) => h.id !== focusedHospital.id)]
    : listData;

  const clinicalServices = kbServices.filter((s) => s.category === "clinical_service");

  return (
    <section id="sec-care" className="scroll-mt-24 space-y-4">
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-md bg-hb-accentSoft text-hb-accentInk flex items-center justify-center shrink-0">
          <Building2 className="w-5 h-5" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-lg font-extrabold text-hb-ink">
            {t.recommended_care_title || "Recommended care options"}
          </h2>
          <p className="text-xs text-hb-muted">{t.care_disclaimer}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7">
          <HospitalList
            hospitals={listData}
            allHospitals={hospitals}
            specialistTypes={specialistTypes}
            urgency={urgency}
            t={t}
            onOpenMap={onSelectHospital}
          />
        </div>
        <div className="lg:col-span-5">
          <HospitalMap hospitals={mapHospitals} />
        </div>
      </div>

      {/* Deep Care Knowledge Base: Specialists, Services & Insurance/Emergency Guidance */}
      {(kbDoctors.length > 0 || clinicalServices.length > 0) && (
        <div className="rounded-2xl bg-hb-surface border border-hb-border shadow-sm p-5 space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {kbDoctors.length > 0 && (
              <div className="lg:col-span-7 space-y-2.5">
                <div className="text-xs font-extrabold uppercase tracking-wider text-hb-ink flex items-center gap-1.5">
                  <Stethoscope className="w-4 h-4 text-hb-accentInk" aria-hidden="true" />
                  <span>Verified Specialist Directory ({kbDoctors.length} specialties)</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {kbDoctors.slice(0, 6).map((doc: any) => (
                    <div
                      key={doc.id}
                      className="rounded-xl bg-hb-subtle border border-hb-border p-3 space-y-1"
                    >
                      <div className="text-xs font-extrabold text-hb-ink">{doc.name}</div>
                      <div className="text-[11px] text-hb-muted">{doc.subspecialty}</div>
                      <div className="text-[11px] text-hb-ink font-medium">
                        Covers: {(doc.conditions_covered || []).slice(0, 3).join(", ")}
                      </div>
                      {doc.available_at_hospitals?.length > 0 && (
                        <div className="text-[10px] text-hb-muted truncate">
                          At {doc.available_at_hospitals.length} verified hospitals
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="lg:col-span-5 space-y-3">
              {clinicalServices.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-extrabold uppercase tracking-wider text-hb-ink flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-hb-lowInk" aria-hidden="true" />
                    <span>Available Hospital Services ({clinicalServices.length})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {clinicalServices.slice(0, 14).map((srv: any) => (
                      <span
                        key={srv.id}
                        className="px-2.5 py-1 rounded-full bg-hb-subtle border border-hb-border text-[11px] font-semibold text-hb-ink capitalize"
                      >
                        {srv.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {kbCareFaqs.length > 0 && (
                <div className="space-y-2 pt-1">
                  {kbCareFaqs.slice(0, 2).map((faq: any) => (
                    <div
                      key={faq.id}
                      className="rounded-xl bg-hb-subtle/70 border border-hb-border p-3 space-y-1"
                    >
                      <div className="text-xs font-extrabold text-hb-ink">{faq.title}</div>
                      <p className="text-[11px] text-hb-muted leading-snug">{faq.summary}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
