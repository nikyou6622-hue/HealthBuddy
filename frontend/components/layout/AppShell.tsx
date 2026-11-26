"use client";

import React from "react";
import { DisclaimerBanner } from "@/components/banners/DisclaimerBanner";
import { Sidebar, NavItemDef } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

interface AppShellProps {
  disclaimerText: string;
  disclaimerCollapsedLabel: string;
  navItems: NavItemDef[];
  activeNav: string;
  onSelectNav: (key: string) => void;
  lang: "en" | "hi";
  onToggleLang: () => void;
  langLabel: string;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  moreLabel: string;
  tagline: string;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  searchPlaceholder: string;
  onOpenChat: () => void;
  askLabel: string;
  onDownloadPdf: () => void;
  downloadLabel: string;
  userEmail: string | null;
  onOpenAccount: () => void;
  children: React.ReactNode;
}

export function AppShell({
  disclaimerText,
  disclaimerCollapsedLabel,
  navItems,
  activeNav,
  onSelectNav,
  lang,
  onToggleLang,
  langLabel,
  darkMode,
  onToggleDarkMode,
  moreLabel,
  tagline,
  searchQuery,
  onSearchChange,
  searchPlaceholder,
  onOpenChat,
  askLabel,
  onDownloadPdf,
  downloadLabel,
  userEmail,
  onOpenAccount,
  children,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-warm-canvas text-hb-ink flex flex-col relative overflow-x-hidden">
      {/* Warm golden flowing ribbons backdrop */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 dark:hidden" aria-hidden="true">
        <svg className="absolute -top-8 -right-8 w-[640px] h-[480px] opacity-65" viewBox="0 0 720 580" fill="none">
          <path
            d="M220 0 C 360 90, 490 35, 570 145 C 660 265, 550 385, 720 440 L 720 0 Z"
            fill="url(#hbTopFluid)"
          />
          <defs>
            <linearGradient id="hbTopFluid" x1="220" y1="0" x2="720" y2="440" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFEAA7" stopOpacity="0.35" />
              <stop offset="55%" stopColor="#FFD56B" stopOpacity="0.65" />
              <stop offset="100%" stopColor="#FFC83D" stopOpacity="0.55" />
            </linearGradient>
          </defs>
        </svg>
        <svg className="absolute -bottom-16 -left-16 w-[500px] h-[380px] opacity-45" viewBox="0 0 550 450" fill="none">
          <path
            d="M0 450 L0 190 C 140 230, 260 130, 360 270 C 440 385, 390 450, 550 450 Z"
            fill="url(#hbBotFluid)"
          />
          <defs>
            <linearGradient id="hbBotFluid" x1="0" y1="190" x2="550" y2="450" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFD54F" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#FFF5CC" stopOpacity="0.2" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <DisclaimerBanner text={disclaimerText} collapsedLabel={disclaimerCollapsedLabel} />

      <div className="flex-1 max-w-[1360px] w-full mx-auto flex flex-col lg:flex-row gap-6 px-4 py-5 pb-24 lg:pb-8 relative z-10">
        <Sidebar
          navItems={navItems}
          activeNav={activeNav}
          onSelectNav={onSelectNav}
          lang={lang}
          onToggleLang={onToggleLang}
          langLabel={langLabel}
          darkMode={darkMode}
          onToggleDarkMode={onToggleDarkMode}
          moreLabel={moreLabel}
          tagline={tagline}
        />

        <main className="flex-1 min-w-0 space-y-5">
          <Topbar
            searchQuery={searchQuery}
            onSearchChange={onSearchChange}
            searchPlaceholder={searchPlaceholder}
            onOpenChat={onOpenChat}
            askLabel={askLabel}
            onDownloadPdf={onDownloadPdf}
            downloadLabel={downloadLabel}
            onToggleLang={onToggleLang}
            langLabel={langLabel}
            userEmail={userEmail}
            onOpenAccount={onOpenAccount}
          />
          {children}
        </main>
      </div>
    </div>
  );
}

