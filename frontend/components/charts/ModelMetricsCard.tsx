"use client";

import React from "react";

interface MetricsProps {
  metrics: {
    model_name?: string;
    accuracy?: number;
    roc_auc?: number;
    f1_weighted?: number;
    sensitivity?: number;
    specificity?: number;
    ppv?: number;
    npv?: number;
  };
}

export function ModelMetricsCard({ metrics }: MetricsProps) {
  const items = [
    { label: "Sensitivity (Recall)", value: metrics.sensitivity },
    { label: "Specificity", value: metrics.specificity },
    { label: "PPV (Precision)", value: metrics.ppv },
    { label: "NPV", value: metrics.npv },
    { label: "ROC-AUC", value: metrics.roc_auc },
    { label: "Accuracy", value: metrics.accuracy },
  ];

  return (
    <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-extrabold uppercase tracking-wider text-slate-500">
          Model Clinical Trust Metrics
        </span>
        <span className="text-xs font-mono font-bold text-sky-600">
          {(metrics.model_name || "Champion").replace(/_/g, " ")}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        {items.map((item) => {
          const val = item.value != null ? item.value * 100 : null;
          return (
            <div key={item.label} className="bg-white dark:bg-slate-900 rounded-xl p-2.5 border border-slate-200 dark:border-slate-800">
              <div className="text-[11px] text-slate-500">{item.label}</div>
              <div className="text-sm font-extrabold mt-0.5">
                {val != null ? `${val.toFixed(1)}%` : "N/A"}
              </div>
              <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full mt-1.5 overflow-hidden">
                <div
                  className="h-full bg-sky-600 rounded-full"
                  style={{ width: `${val != null ? Math.min(100, val) : 0}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

