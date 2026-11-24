"use client";

import React, { useState } from "react";
import { DataOriginBadge } from "@/components/ScientificBadges";
import type { BioprocessTimePoint, DataOrigin } from "@/lib/mockBioprocess";

interface BioprocessChartsProps {
  data: BioprocessTimePoint[];
  origin: DataOrigin;
}

interface DualChartConfig {
  id: string;
  title: string;
  subtitle: string;
  primaryLabel: string;
  primaryUnit: string;
  primaryColor: string;
  primaryMin: number;
  primaryMax: number;
  getPrimary: (p: BioprocessTimePoint) => number;
  secondaryLabel: string;
  secondaryUnit: string;
  secondaryColor: string;
  secondaryMin: number;
  secondaryMax: number;
  getSecondary: (p: BioprocessTimePoint) => number;
}

const CHART_CONFIGS: DualChartConfig[] = [
  {
    id: "temp-ph",
    title: "Thermal & pH Stability",
    subtitle: "Jacket Loop Control vs. Alkali Titration",
    primaryLabel: "Temp",
    primaryUnit: "°C",
    primaryColor: "#22D3EE",
    primaryMin: 36.0,
    primaryMax: 37.6,
    getPrimary: (p) => p.temperatureC,
    secondaryLabel: "pH",
    secondaryUnit: "pH",
    secondaryColor: "#34D399",
    secondaryMin: 6.85,
    secondaryMax: 7.25,
    getSecondary: (p) => p.ph,
  },
  {
    id: "do-rpm",
    title: "Oxygenation & Agitation Cascade",
    subtitle: "Dissolved Oxygen (%sat) vs. Impeller Speed (RPM)",
    primaryLabel: "dO₂",
    primaryUnit: "%sat",
    primaryColor: "#38BDF8",
    primaryMin: 25,
    primaryMax: 105,
    getPrimary: (p) => p.dissolvedOxygenPct,
    secondaryLabel: "Agitation",
    secondaryUnit: "RPM",
    secondaryColor: "#A78BFA",
    secondaryMin: 120,
    secondaryMax: 240,
    getSecondary: (p) => p.agitationRpm,
  },
  {
    id: "biomass-glucose",
    title: "Biomass Growth & Nutrient Uptake",
    subtitle: "Dry Cell Weight vs. Residual Glucose",
    primaryLabel: "Biomass",
    primaryUnit: "g/L",
    primaryColor: "#10B981",
    primaryMin: 0,
    primaryMax: 20,
    getPrimary: (p) => p.biomassGL,
    secondaryLabel: "Glucose",
    secondaryUnit: "g/L",
    secondaryColor: "#FBBF24",
    secondaryMin: 0,
    secondaryMax: 26,
    getSecondary: (p) => p.glucoseGL,
  },
  {
    id: "titer-eff",
    title: "Product Yield & Process Efficiency",
    subtitle: "mAb Volumetric Titer vs. OTR/OUR Efficiency",
    primaryLabel: "Titer",
    primaryUnit: "g/L",
    primaryColor: "#22D3EE",
    primaryMin: 0,
    primaryMax: 5.2,
    getPrimary: (p) => p.titerGL,
    secondaryLabel: "Efficiency",
    secondaryUnit: "%",
    secondaryColor: "#34D399",
    secondaryMin: 70,
    secondaryMax: 100,
    getSecondary: (p) => p.efficiencyPct,
  },
];

function DualSeriesCard({
  cfg,
  data,
  origin,
}: {
  cfg: DualChartConfig;
  data: BioprocessTimePoint[];
  origin: DataOrigin;
}) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const w = 440;
  const h = 160;
  const padX = 12;
  const padY = 14;
  const plotW = w - padX * 2;
  const plotH = h - padY * 2;

  const toX = (i: number) => padX + (i / Math.max(1, data.length - 1)) * plotW;
  const toY = (val: number, min: number, max: number) => {
    const norm = (val - min) / Math.max(0.0001, max - min);
    return h - padY - Math.max(0, Math.min(1, norm)) * plotH;
  };

  const primaryPts = data.map((pt, i) => ({
    x: toX(i),
    y: toY(cfg.getPrimary(pt), cfg.primaryMin, cfg.primaryMax),
  }));
  const secondaryPts = data.map((pt, i) => ({
    x: toX(i),
    y: toY(cfg.getSecondary(pt), cfg.secondaryMin, cfg.secondaryMax),
  }));

  const pathA = primaryPts
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
  const pathB = secondaryPts
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  const activeIdx = hoverIdx !== null ? hoverIdx : data.length - 1;
  const activePt = data[activeIdx];

  return (
    <div className="sb-surface rounded-2xl p-5 flex flex-col justify-between">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <h4 className="text-sm font-display font-semibold text-slate-100">{cfg.title}</h4>
          <p className="text-[11px] font-mono text-slate-400">{cfg.subtitle}</p>
        </div>
        <DataOriginBadge origin={origin} />
      </div>

      <div className="relative">
        <svg
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-40 overflow-visible"
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* Horizontal grid lines */}
          {[0.25, 0.5, 0.75].map((f) => (
            <line
              key={f}
              x1={padX}
              y1={padY + plotH * f}
              x2={w - padX}
              y2={padY + plotH * f}
              stroke="rgba(148,163,184,0.1)"
              strokeDasharray="3 3"
            />
          ))}

          {/* Animated SVG Curves */}
          <path
            d={pathA}
            fill="none"
            stroke={cfg.primaryColor}
            strokeWidth="2.2"
          />
          <path
            d={pathB}
            fill="none"
            stroke={cfg.secondaryColor}
            strokeWidth="2"
            strokeDasharray="4 3"
          />

          {/* Active hover vertical marker & points */}
          {activeIdx !== null && primaryPts[activeIdx] && (
            <>
              <line
                x1={primaryPts[activeIdx].x}
                y1={padY}
                x2={primaryPts[activeIdx].x}
                y2={h - padY}
                stroke="rgba(148,163,184,0.3)"
                strokeWidth="1"
              />
              <circle
                cx={primaryPts[activeIdx].x}
                cy={primaryPts[activeIdx].y}
                r="4"
                fill={cfg.primaryColor}
              />
              <circle
                cx={secondaryPts[activeIdx].x}
                cy={secondaryPts[activeIdx].y}
                r="3.5"
                fill={cfg.secondaryColor}
              />
            </>
          )}

          {/* Invisible hover columns */}
          {data.map((_, i) => (
            <rect
              key={i}
              x={toX(i) - plotW / (data.length * 2)}
              y={0}
              width={plotW / data.length}
              height={h}
              fill="transparent"
              onMouseEnter={() => setHoverIdx(i)}
              className="cursor-crosshair"
            />
          ))}
        </svg>
      </div>

      {/* Interactive Telemetry Readout Footer */}
      {activePt && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono sb-tabular">
          <span className="text-slate-400">
            t = <strong className="text-slate-200">{activePt.hour} h</strong>
          </span>
          <div className="flex items-center gap-4">
            <span style={{ color: cfg.primaryColor }}>
              ● {cfg.primaryLabel}:{" "}
              <strong>
                {cfg.getPrimary(activePt).toFixed(2)} {cfg.primaryUnit}
              </strong>
            </span>
            <span style={{ color: cfg.secondaryColor }}>
              --- {cfg.secondaryLabel}:{" "}
              <strong>
                {cfg.getSecondary(activePt).toFixed(2)} {cfg.secondaryUnit}
              </strong>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export function BioprocessCharts({ data, origin }: BioprocessChartsProps) {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
      {CHART_CONFIGS.map((cfg) => (
        <DualSeriesCard key={cfg.id} cfg={cfg} data={data} origin={origin} />
      ))}
    </div>
  );
}
