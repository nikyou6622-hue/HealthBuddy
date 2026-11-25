"use client";

import React from "react";
import { ShieldAlert } from "lucide-react";

export function DisclaimerBanner({ text }: { text: string }) {
  return (
    <div
      role="status"
      className="w-full bg-[#3B2F10]/95 backdrop-blur-sm text-[#FFF9E3] text-[11.5px] sm:text-xs py-2 px-4 flex items-center justify-center gap-2 border-b border-[#5E4C19] shadow-xs relative z-30"
    >
      <ShieldAlert className="w-3.5 h-3.5 text-[#FFC83D] shrink-0" strokeWidth={2.2} />
      <span className="font-medium text-center">{text}</span>
    </div>
  );
}
