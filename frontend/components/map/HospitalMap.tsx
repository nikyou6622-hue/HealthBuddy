"use client";

import React, { useState } from "react";
import { ExternalLink, MapPin } from "lucide-react";

interface HospitalItem {
  id: number;
  name: string;
  city: string;
  lat?: number | null;
  lon?: number | null;
}

export function HospitalMap({ hospitals }: { hospitals: HospitalItem[] }) {
  const mappable = hospitals.filter((h) => h.lat != null && h.lon != null);
  const [selectedId, setSelectedId] = useState<number | null>(mappable[0]?.id ?? null);

  if (mappable.length === 0) {
    return null;
  }

  const active = mappable.find((h) => h.id === selectedId) || mappable[0];
  const lat = active.lat!;
  const lon = active.lon!;
  const delta = 0.035;
  const bbox = `${lon - delta},${lat - delta},${lon + delta},${lat + delta}`;
  const osmEmbed = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lon}`;
  const osmLink = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=14/${lat}/${lon}`;

  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
      <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-bold">
          <MapPin className="w-4 h-4 text-sky-600" />
          <span>Verified Hospital Map (OpenStreetMap)</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {mappable.slice(0, 5).map((h) => (
            <button
              key={h.id}
              onClick={() => setSelectedId(h.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                h.id === active.id
                  ? "bg-sky-600 text-white"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
              }`}
            >
              {h.name.split(" ").slice(0, 2).join(" ")}
            </button>
          ))}
        </div>
      </div>
      <iframe
        title={`Map of ${active.name}`}
        src={osmEmbed}
        className="w-full h-64 border-0"
        loading="lazy"
      />
      <div className="px-4 py-2.5 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs text-slate-500">
        <span>
          Focused on <strong>{active.name}</strong> ({active.city})
        </span>
        <a
          href={osmLink}
          target="_blank"
          rel="noreferrer"
          className="text-sky-600 font-bold inline-flex items-center gap-1 hover:underline"
        >
          Open in OpenStreetMap <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}

