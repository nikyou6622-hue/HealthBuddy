"use client";

import React, { useEffect, useState } from "react";
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

  useEffect(() => {
    if (mappable.length > 0) {
      setSelectedId(mappable[0].id);
    }
  }, [mappable[0]?.id]);

  if (mappable.length === 0) {
    return (
      <div className="rounded-2xl bg-hb-surface border border-hb-border p-5 text-xs text-hb-muted shadow-sm">
        Hospital coordinates are loading or unavailable for the current filter.
      </div>
    );
  }

  const active = mappable.find((h) => h.id === selectedId) || mappable[0];
  const lat = active.lat!;
  const lon = active.lon!;
  const delta = 0.035;
  const bbox = `${lon - delta},${lat - delta},${lon + delta},${lat + delta}`;
  const osmEmbed = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lon}`;
  const osmLink = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=14/${lat}/${lon}`;

  return (
    <div className="rounded-2xl bg-hb-surface border border-hb-border overflow-hidden shadow-sm">
      <div className="p-3.5 border-b border-hb-border flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-extrabold text-hb-ink">
          <MapPin className="w-4 h-4 text-hb-accentInk" aria-hidden="true" />
          <span>Verified Hospital Map (OpenStreetMap)</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {mappable.slice(0, 5).map((h) => (
            <button
              key={h.id}
              type="button"
              onClick={() => setSelectedId(h.id)}
              className={`px-2.5 py-1 rounded-full text-xs font-bold border transition ${
                h.id === active.id
                  ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                  : "bg-hb-subtle text-hb-muted border-hb-border hover:text-hb-ink"
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
        className="w-full h-64 sm:h-72 border-0"
        loading="lazy"
      />
      <div className="px-4 py-2.5 bg-hb-subtle border-t border-hb-border flex flex-wrap items-center justify-between gap-2 text-xs text-hb-muted">
        <span>
          Focused on <strong className="text-hb-ink">{active.name}</strong> ({active.city})
        </span>
        <a
          href={osmLink}
          target="_blank"
          rel="noreferrer"
          className="text-hb-accentInk font-bold inline-flex items-center gap-1 hover:underline"
        >
          Open in OpenStreetMap <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}
