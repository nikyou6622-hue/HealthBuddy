"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, ShieldAlert } from "lucide-react";

interface DisclaimerBannerProps {
  text: string;
  collapsedLabel?: string;
}

export function DisclaimerBanner({
  text,
  collapsedLabel = "Educational screening tool — view disclaimer",
}: DisclaimerBannerProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      role="status"
      className="w-full bg-[#3B2F10]/95 backdrop-blur-sm border-b border-[#5E4C19] text-[#FFF9E3] text-xs py-1.5 px-4 flex items-center justify-center gap-2 relative z-30 transition-colors duration-150"
    >
      <ShieldAlert className="w-3.5 h-3.5 text-[#FFC83D] shrink-0" strokeWidth={2.2} aria-hidden="true" />
      <span className="font-medium text-center truncate max-w-3xl">
        {collapsed ? collapsedLabel : text}
      </span>
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        aria-expanded={!collapsed}
        aria-label={collapsed ? "Expand medical disclaimer" : "Collapse medical disclaimer"}
        className="ml-1 px-2 py-0.5 rounded-full text-[11px] font-semibold text-[#FFE89E] hover:text-white hover:bg-white/10 inline-flex items-center gap-1 shrink-0 focus:outline-none focus:ring-2 focus:ring-hb-accent transition"
      >
        {collapsed ? (
          <ChevronDown className="w-3.5 h-3.5" aria-hidden="true" />
        ) : (
          <ChevronUp className="w-3.5 h-3.5" aria-hidden="true" />
        )}
      </button>
    </div>
  );
}
