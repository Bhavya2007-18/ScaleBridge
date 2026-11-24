"use client";

import React from "react";
import dynamic from "next/dynamic";
import { MeasurementSeries } from "@/lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export interface BatchOverlaySeries {
  batchRunCode: string;
  series: MeasurementSeries[];
}

const COLORS = [
  "#22D3EE", // cyan-400
  "#34D399", // bioluminescent emerald-400
  "#FBBF24", // amber-400
  "#A78BFA", // violet-400
];

export function BatchTrendChart({
  batches,
  selectedVariables,
}: {
  batches: BatchOverlaySeries[];
  selectedVariables: string[];
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {selectedVariables.map((varKey) => {
        const traces: Array<Record<string, unknown>> = [];
        let unitLabel = "";

        batches.forEach((b, bIdx) => {
          const found = b.series.find((s) => s.variable === varKey);
          if (!found) return;
          unitLabel = found.unit_display;
          const validPts = found.points.filter((p) => p.quality_flag !== "invalid");
          traces.push({
            x: validPts.map((p) => p.elapsed_h),
            y: validPts.map((p) => p.value),
            type: "scatter",
            mode: "lines+markers",
            name: b.batchRunCode,
            line: {
              color: COLORS[bIdx % COLORS.length],
              width: 2,
              dash: bIdx % 2 === 1 ? "dash" : "solid",
            },
            marker: { size: 4 },
            connectgaps: false, // Never interpolate across missing data gaps (FR-DB-03)
          });
        });

        return (
          <div key={varKey} className="sb-surface rounded-xl p-4">
            <div className="flex items-center justify-between mb-2 px-1">
              <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">
                {varKey.replace(/_/g, " ")}
              </h4>
              <span className="font-mono text-[11px] text-slate-400">
                Unit: {unitLabel || "N/A"} · Elapsed Time (h)
              </span>
            </div>
            {traces.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-xs font-mono text-slate-500">
                No measurement series available for {varKey}
              </div>
            ) : (
              <Plot
                data={traces as never[]}
                layout={{
                  autosize: true,
                  height: 240,
                  margin: { l: 50, r: 16, t: 16, b: 40 },
                  xaxis: {
                    title: { text: "Elapsed Fermentation Time (h)", font: { size: 11, color: "#94A3B8" } },
                    gridcolor: "rgba(148, 163, 184, 0.08)",
                    tickfont: { size: 10, color: "#94A3B8" },
                    zerolinecolor: "rgba(148, 163, 184, 0.15)",
                  },
                  yaxis: {
                    title: { text: unitLabel, font: { size: 11, color: "#94A3B8" } },
                    gridcolor: "rgba(148, 163, 184, 0.08)",
                    tickfont: { size: 10, color: "#94A3B8" },
                    zerolinecolor: "rgba(148, 163, 184, 0.15)",
                  },
                  legend: { orientation: "h", y: 1.15, x: 0, font: { size: 10, color: "#CBD5E1" } },
                  paper_bgcolor: "transparent",
                  plot_bgcolor: "rgba(3, 6, 12, 0.65)",
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: "100%" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
