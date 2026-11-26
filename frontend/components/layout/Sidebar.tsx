"use client";

import React, { useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Languages,
  LucideIcon,
  Menu,
  Moon,
  Sun,
  X,
} from "lucide-react";

export type NavItemDef = {
  key: string;
  label: string;
  Icon: LucideIcon;
};

interface SidebarProps {
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
}

export function Sidebar({
  navItems,
  activeNav,
  onSelectNav,
  onToggleLang,
  langLabel,
  darkMode,
  onToggleDarkMode,
  moreLabel,
  tagline,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const primaryMobile = navItems.slice(0, 4);
  const secondaryMobile = navItems.slice(4);

  return (
    <>
      {/* Desktop Collapsible Sidebar */}
      <aside
        aria-label="Primary sidebar"
        className={`hidden lg:flex flex-col shrink-0 transition-all duration-200 ${
          collapsed ? "w-[76px]" : "w-[220px]"
        }`}
      >
        <div className="sticky top-4 relative overflow-hidden rounded-2xl bg-hb-surface border border-hb-border shadow-sm flex flex-col justify-between min-h-[calc(100vh-4.5rem)]">
          {/* Amber wave accent at top */}
          <div className="absolute top-0 inset-x-0 h-32 pointer-events-none overflow-hidden rounded-t-2xl" aria-hidden="true">
            <svg viewBox="0 0 240 120" preserveAspectRatio="none" className="absolute top-0 left-0 w-full h-full opacity-70">
              <path d="M0 0 L240 0 L240 50 Q 180 90, 120 60 T 0 70 Z" fill="url(#sidebarWave)" />
              <defs>
                <linearGradient id="sidebarWave" x1="0" y1="0" x2="240" y2="120" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#FFE066" stopOpacity="0.75" />
                  <stop offset="100%" stopColor="#FFC83D" stopOpacity="0.3" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div className="p-3 flex flex-col gap-5 relative z-10 flex-1">
            {/* Brand Header */}
            <div className={`flex items-center ${collapsed ? "justify-center" : "justify-between"} pt-2 px-1`}>
              <div className="flex items-center gap-2.5 min-w-0">
                {/* Logo with heart + ECG icon */}
                <div className="w-10 h-10 rounded-xl bg-hb-cta flex items-center justify-center shrink-0 shadow-sm">
                  <svg viewBox="0 0 36 36" fill="none" className="w-6 h-6" aria-hidden="true">
                    <path d="M18 28 C18 28 7 20 7 13.5 C7 10 9.8 7 13.5 7 C15.6 7 17.5 8.2 18 9.5 C18.5 8.2 20.4 7 22.5 7 C26.2 7 29 10 29 13.5 C29 20 18 28 18 28Z" fill="#2B2208" />
                    <path d="M6 18 L10 18 L12 14 L14 22 L16 16 L18 20 L20 18 L30 18" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                {!collapsed && (
                  <div className="min-w-0">
                    <div className="font-extrabold text-base tracking-tight text-hb-ink truncate leading-tight">
                      HealthBuddy
                    </div>
                    <div className="text-[11px] font-medium text-hb-muted truncate">{tagline}</div>
                  </div>
                )}
              </div>
              {!collapsed && (
                <button
                  type="button"
                  onClick={() => setCollapsed(true)}
                  aria-label="Collapse sidebar"
                  className="w-7 h-7 rounded-lg text-hb-muted hover:text-hb-ink hover:bg-hb-subtle flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-hb-accent"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              )}
            </div>

            {collapsed && (
              <button
                type="button"
                onClick={() => setCollapsed(false)}
                aria-label="Expand sidebar"
                className="w-full h-9 rounded-lg text-hb-muted hover:text-hb-ink hover:bg-hb-subtle flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-hb-accent"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            )}

            {/* Navigation Links */}
            <nav aria-label="Main navigation" className="flex flex-col gap-1">
              {navItems.map(({ key, label, Icon }) => {
                const isActive = activeNav === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => onSelectNav(key)}
                    aria-current={isActive ? "page" : undefined}
                    title={collapsed ? label : undefined}
                    className={`min-h-[44px] px-3 py-2.5 rounded-xl text-sm font-semibold inline-flex items-center ${
                      collapsed ? "justify-center" : "gap-3"
                    } focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors duration-150 ${
                      isActive
                        ? "bg-hb-cta text-hb-ctaInk font-bold shadow-sm"
                        : "text-hb-muted hover:bg-hb-subtle hover:text-hb-ink"
                    }`}
                  >
                    <Icon className="w-[18px] h-[18px] shrink-0" strokeWidth={isActive ? 2.5 : 2} />
                    {!collapsed && <span className="truncate">{label}</span>}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Footer: dark/lang controls */}
          <div className="p-3 space-y-2 relative z-10">
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={onToggleDarkMode}
                aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
                title={collapsed ? (darkMode ? "Light mode" : "Dark mode") : undefined}
                className={`flex-1 min-h-[36px] px-2 py-1.5 rounded-xl bg-hb-subtle hover:bg-hb-border/60 text-hb-ink text-xs font-semibold inline-flex items-center ${
                  collapsed ? "justify-center" : "gap-2"
                } focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors`}
              >
                {darkMode ? <Sun className="w-3.5 h-3.5 shrink-0" /> : <Moon className="w-3.5 h-3.5 shrink-0" />}
                {!collapsed && <span>{darkMode ? "Light" : "Dark"}</span>}
              </button>
              <button
                type="button"
                onClick={onToggleLang}
                aria-label="Toggle language"
                title={collapsed ? langLabel : undefined}
                className={`flex-1 min-h-[36px] px-2 py-1.5 rounded-xl bg-hb-subtle hover:bg-hb-border/60 text-hb-ink text-xs font-semibold inline-flex items-center ${
                  collapsed ? "justify-center" : "gap-2"
                } focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors`}
              >
                <Languages className="w-3.5 h-3.5 shrink-0" />
                {!collapsed && <span>{langLabel}</span>}
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Fixed Bottom Tab Bar */}
      <nav
        aria-label="Mobile navigation"
        className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-hb-surface/97 backdrop-blur-md border-t border-hb-border px-2 py-1.5 flex items-center justify-around"
      >
        {primaryMobile.map(({ key, label, Icon }) => {
          const isActive = activeNav === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => {
                onSelectNav(key);
                setMobileDrawerOpen(false);
              }}
              aria-current={isActive ? "page" : undefined}
              className={`min-h-[44px] flex-1 px-1.5 py-1 rounded-xl flex flex-col items-center justify-center gap-0.5 text-[11px] font-semibold focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors ${
                isActive ? "text-hb-ctaInk bg-hb-cta font-bold" : "text-hb-muted"
              }`}
            >
              <Icon className="w-4 h-4" strokeWidth={2} />
              <span className="truncate max-w-[70px]">{label}</span>
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => setMobileDrawerOpen((v) => !v)}
          aria-expanded={mobileDrawerOpen}
          className="min-h-[44px] flex-1 px-1.5 py-1 rounded-xl flex flex-col items-center justify-center gap-0.5 text-[11px] font-semibold text-hb-muted focus:outline-none focus:ring-2 focus:ring-hb-accent"
        >
          <Menu className="w-4 h-4" strokeWidth={2} />
          <span>{moreLabel}</span>
        </button>
      </nav>

      {/* Mobile Overflow Drawer */}
      {mobileDrawerOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="More navigation options"
          className="lg:hidden fixed inset-0 z-50 bg-black/40 flex items-end"
          onClick={() => setMobileDrawerOpen(false)}
        >
          <div
            className="w-full rounded-t-2xl bg-hb-surface border-t border-hb-border p-4 pb-8 space-y-2"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-2 border-b border-hb-border">
              <span className="font-bold text-sm text-hb-ink">HealthBuddy</span>
              <button
                type="button"
                onClick={() => setMobileDrawerOpen(false)}
                aria-label="Close menu"
                className="w-9 h-9 rounded-xl flex items-center justify-center text-hb-muted hover:text-hb-ink"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-1 gap-1.5">
              {secondaryMobile.map(({ key, label, Icon }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => {
                    onSelectNav(key);
                    setMobileDrawerOpen(false);
                  }}
                  className={`min-h-[44px] px-3 py-2 rounded-xl text-sm font-semibold inline-flex items-center gap-3 ${
                    activeNav === key
                      ? "bg-hb-cta text-hb-ctaInk font-bold"
                      : "text-hb-ink hover:bg-hb-subtle"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </button>
              ))}
              <button
                type="button"
                onClick={onToggleDarkMode}
                className="min-h-[44px] px-3 py-2 rounded-xl text-sm font-semibold text-hb-ink hover:bg-hb-subtle inline-flex items-center gap-3"
              >
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                <span>{darkMode ? "Light mode" : "Dark mode"}</span>
              </button>
              <button
                type="button"
                onClick={onToggleLang}
                className="min-h-[44px] px-3 py-2 rounded-xl text-sm font-semibold text-hb-ink hover:bg-hb-subtle inline-flex items-center gap-3"
              >
                <Languages className="w-4 h-4" />
                <span>{langLabel}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
