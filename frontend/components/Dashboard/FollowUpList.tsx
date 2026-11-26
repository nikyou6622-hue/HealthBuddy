"use client";

import React from "react";
import { CalendarClock, ClipboardList, Download } from "lucide-react";

interface FollowUpItem {
  condition: string;
  tier: string;
  due_date: string;
}

interface FollowUpListProps {
  followups: FollowUpItem[];
  lang: "en" | "hi";
  t: Record<string, string>;
  onDownloadPdf?: () => void;
  compact?: boolean;
}

export function FollowUpList({
  followups,
  lang,
  t,
  onDownloadPdf,
  compact = false,
}: FollowUpListProps) {
  return (
    <div className="space-y-4">
      {!compact && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-md bg-hb-accentSoft text-hb-accentInk flex items-center justify-center shrink-0">
              <CalendarClock className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-hb-ink">
                {t.sticky_followup || "Follow-up"}
              </h2>
              <p className="text-xs text-hb-muted">Recommended clinical review timeline</p>
            </div>
          </div>
          {onDownloadPdf && (
            <button
              type="button"
              onClick={onDownloadPdf}
              className="min-h-[42px] px-4 py-2 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-xs font-extrabold inline-flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
            >
              <Download className="w-4 h-4" aria-hidden="true" />
              <span>{t.btn_download_pdf || "Download PDF"}</span>
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 tabular-nums">
        {followups.map((fu) => {
          const d = new Date(fu.due_date);
          const isValid = !Number.isNaN(d.getTime());
          const formatted = isValid
            ? new Intl.DateTimeFormat(lang === "hi" ? "hi-IN" : "en-IN", {
                year: "numeric",
                month: "short",
                day: "numeric",
              }).format(d)
            : fu.due_date;
          const daysLeft = isValid
            ? Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
            : null;
          const tierBadge =
            fu.tier === "high"
              ? "bg-hb-highBg text-hb-highInk border-hb-highBorder"
              : fu.tier === "moderate"
              ? "bg-hb-modBg text-hb-modInk border-hb-modBorder"
              : "bg-hb-lowBg text-hb-lowInk border-hb-lowBorder";

          return (
            <div
              key={fu.condition}
              className="rounded-md bg-hb-subtle border border-hb-border p-3.5 flex items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="font-bold text-sm capitalize text-hb-ink">{fu.condition}</div>
                <span
                  className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-bold uppercase border ${tierBadge}`}
                >
                  {fu.tier}
                </span>
              </div>
              <div className="text-right">
                <div className="text-xs font-extrabold text-hb-ink">{formatted}</div>
                {daysLeft !== null && daysLeft > 0 && (
                  <div className="text-[11px] font-medium text-hb-muted">In {daysLeft} days</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded-md bg-hb-subtle border border-hb-border p-3.5 flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-xs font-bold text-hb-ink">
          <ClipboardList className="w-4 h-4 text-hb-accent" aria-hidden="true" />
          <span>Visit checklist:</span>
        </span>
        <div className="flex flex-wrap gap-2 text-xs text-hb-muted">
          <span className="px-2.5 py-0.5 rounded-full bg-hb-surface border border-hb-border">
            PDF summary
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-hb-surface border border-hb-border">
            Recent lab reports
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-hb-surface border border-hb-border">
            Current medication list
          </span>
        </div>
      </div>
    </div>
  );
}

