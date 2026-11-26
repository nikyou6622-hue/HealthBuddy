"use client";

import React from "react";
import { Download, Languages, RefreshCw, Search } from "lucide-react";

interface TopbarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  searchPlaceholder: string;
  onOpenChat: () => void;
  askLabel: string;
  onDownloadPdf: () => void;
  downloadLabel: string;
  onToggleLang: () => void;
  langLabel: string;
  userEmail: string | null;
  onOpenAccount: () => void;
}

export function Topbar({
  searchQuery,
  onSearchChange,
  searchPlaceholder,
  onOpenChat,
  askLabel,
  onDownloadPdf,
  downloadLabel,
  onToggleLang,
  langLabel,
  userEmail,
  onOpenAccount,
}: TopbarProps) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-3 pb-1">
      {/* Row 1 on mobile: Brand + quick actions */}
      <div className="flex items-center justify-between gap-2 lg:hidden">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-hb-cta flex items-center justify-center shrink-0 shadow-sm">
            <svg viewBox="0 0 36 36" fill="none" className="w-5 h-5" aria-hidden="true">
              <path d="M18 28 C18 28 7 20 7 13.5 C7 10 9.8 7 13.5 7 C15.6 7 17.5 8.2 18 9.5 C18.5 8.2 20.4 7 22.5 7 C26.2 7 29 10 29 13.5 C29 20 18 28 18 28Z" fill="#2B2208" />
              <path d="M6 18 L10 18 L12 14 L14 22 L16 16 L18 20 L20 18 L30 18" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="font-extrabold text-base text-hb-ink truncate">HealthBuddy</span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={onToggleLang}
            aria-label="Toggle language"
            className="min-h-[40px] px-2.5 py-1.5 rounded-full bg-hb-surface hover:bg-hb-subtle border border-hb-border text-xs font-bold text-hb-ink inline-flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-hb-accent"
          >
            <Languages className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{langLabel}</span>
          </button>

          <button
            type="button"
            onClick={onDownloadPdf}
            aria-label={downloadLabel}
            className="min-h-[40px] px-2.5 py-1.5 rounded-full bg-hb-surface hover:bg-hb-subtle border border-hb-border text-xs font-bold text-hb-ink inline-flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-hb-accent shadow-sm"
          >
            <Download className="w-3.5 h-3.5" strokeWidth={2} aria-hidden="true" />
            <span className="sr-only sm:not-sr-only">{downloadLabel}</span>
          </button>

          <button
            type="button"
            onClick={onOpenAccount}
            aria-label="Account and history"
            className="w-10 h-10 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk font-extrabold text-sm flex items-center justify-center border-2 border-white shadow-sm focus:outline-none focus:ring-2 focus:ring-hb-accent"
          >
            {userEmail ? userEmail[0].toUpperCase() : "A"}
          </button>
        </div>
      </div>

      {/* Search bar (full-width on mobile, inline on desktop) */}
      <div className="relative flex-1 min-w-0 sm:max-w-md">
        <Search className="w-4 h-4 text-hb-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden="true" />
        <input
          type="search"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          className="w-full min-h-[44px] pl-10 pr-4 py-2 rounded-full bg-hb-surface border border-hb-border text-sm text-hb-ink placeholder:text-hb-muted focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors shadow-sm"
        />
      </div>

      {/* Desktop action buttons */}
      <div className="hidden lg:flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={onDownloadPdf}
          className="min-h-[44px] px-3.5 py-2 rounded-full bg-hb-surface hover:bg-hb-subtle border border-hb-border text-xs font-bold text-hb-ink inline-flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors shadow-sm"
        >
          <Download className="w-4 h-4" strokeWidth={2} aria-hidden="true" />
          <span>{downloadLabel}</span>
        </button>

        <button
          type="button"
          onClick={onOpenChat}
          className="min-h-[44px] px-4 py-2 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-xs font-extrabold inline-flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors shadow-sm"
        >
          <RefreshCw className="w-4 h-4" strokeWidth={2.2} aria-hidden="true" />
          <span>{askLabel}</span>
        </button>

        <button
          type="button"
          onClick={onOpenAccount}
          aria-label="Account and history"
          className="w-10 h-10 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk font-extrabold text-sm flex items-center justify-center border-2 border-white shadow-sm focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
        >
          {userEmail ? userEmail[0].toUpperCase() : "A"}
        </button>
      </div>
    </header>
  );
}
