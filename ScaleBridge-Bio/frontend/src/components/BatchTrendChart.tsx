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
  "#0D9488", // teal-600
  "#2563EB", // blue-600
  "#D97706", // amber-600
  "#7C3AED", // violet-600
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
          <div key={varKey} className="bg-white rounded-lg border border-slate-200 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-1 px-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                {varKey.replace(/_/g, " ")}
              </h4>
              <span className="font-mono text-xs text-slate-500">
                Unit: {unitLabel || "N/A"} · Elapsed Time (h)
              </span>
            </div>
            {traces.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-xs text-slate-400">
                No measurement series available for {varKey}
              </div>
            ) : (
              <Plot
                data={traces as never[]}
                layout={{
                  autosize: true,
                  height: 240,
                  margin: { l: 48, r: 16, t: 12, b: 38 },
                  xaxis: { title: { text: "Elapsed Fermentation Time (h)", font: { size: 11 } } },
                  yaxis: { title: { text: unitLabel, font: { size: 11 } } },
                  legend: { orientation: "h", y: 1.14, x: 0, font: { size: 10 } },
                  paper_bgcolor: "transparent",
                  plot_bgcolor: "#f8fafc",
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
