"use client";

import React, { useMemo } from "react";
import {
  computeScaleUpPreview,
  SAMPLE_BIOPROCESS_SERIES,
} from "@/lib/mockBioprocess";
import { DataOriginBadge } from "@/components/ScientificBadges";

interface TelemetryPreviewProps {
  rpm: number;
  aerationVvm: number;
  onRpmChange: (rpm: number) => void;
  onAerationChange: (vvm: number) => void;
}

function buildPolylinePath(
  values: number[],
  width: number,
  height: number,
  minVal: number,
  maxVal: number
): string {
  const padY = 12;
  const usableH = height - padY * 2;
  return values
    .map((v, idx) => {
      const x = (idx / Math.max(1, values.length - 1)) * width;
      const norm = (v - minVal) / Math.max(0.0001, maxVal - minVal);
      const y = height - padY - norm * usableH;
      return `${idx === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function TelemetryPreview({
  rpm,
  aerationVvm,
  onRpmChange,
  onAerationChange,
}: TelemetryPreviewProps) {
  const calc = useMemo(
    () =>
      computeScaleUpPreview({
        sourceVolumeL: 2.0,
        sourceRpm: 420,
        sourceImpellerM: 0.055,
        targetVolumeL: 150.0,
        targetRpm: rpm,
        targetImpellerM: 0.24,
        aerationVvm,
      }),
    [rpm, aerationVvm]
  );

  const biomassPath = useMemo(
    () =>
      buildPolylinePath(
        SAMPLE_BIOPROCESS_SERIES.map((p) => p.biomassGL),
        340,
        110,
        0,
        20
      ),
    []
  );
  const titerPath = useMemo(
    () =>
      buildPolylinePath(
        SAMPLE_BIOPROCESS_SERIES.map((p) => p.titerGL),
        340,
        110,
        0,
        5
      ),
    []
  );
  const doPath = useMemo(
    () =>
      buildPolylinePath(
        SAMPLE_BIOPROCESS_SERIES.map((p) => p.dissolvedOxygenPct),
        340,
        110,
        20,
        105
      ),
    []
  );
  const glucosePath = useMemo(
    () =>
      buildPolylinePath(
        SAMPLE_BIOPROCESS_SERIES.map((p) => p.glucoseGL),
        340,
        110,
        0,
        26
      ),
    []
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
      {/* Left: Interactive Digital Twin Parameter Sliders & Deterministic Readouts */}
      <div className="lg:col-span-5 sb-surface rounded-2xl p-6 flex flex-col justify-between space-y-6">
        <div>
          <div className="flex items-center justify-between gap-2 mb-4">
            <span className="text-[11px] font-mono uppercase tracking-widest text-cyan-400">
              Live Hydrodynamic Coupling
            </span>
            <DataOriginBadge origin="simulated" />
          </div>
          <h3 className="text-xl font-display font-bold text-slate-100">
            Tune Operating Parameters on the 3D Twin
          </h3>
          <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
            Adjust pilot vessel agitation and aeration sparging below. The 3D reactor impeller, liquid vortex, and bubble dynamics update in real time alongside deterministic physics.
          </p>
        </div>

        <div className="space-y-5">
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-slate-300">Agitation Speed (N)</span>
              <span className="text-cyan-300 font-semibold sb-tabular">{rpm} RPM</span>
            </div>
            <input
              type="range"
              min={60}
              max={240}
              step={5}
              value={rpm}
              onChange={(e) => onRpmChange(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
              <span>60 RPM (Low Shear)</span>
              <span>240 RPM (Drive Max)</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-slate-300">Aeration Flow Rate (VVM)</span>
              <span className="text-emerald-300 font-semibold sb-tabular">
                {aerationVvm.toFixed(2)} vvm
              </span>
            </div>
            <input
              type="range"
              min={0.15}
              max={1.2}
              step={0.05}
              value={aerationVvm}
              onChange={(e) => onAerationChange(Number(e.target.value))}
              className="w-full accent-emerald-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
              <span>0.15 vvm</span>
              <span>1.20 vvm</span>
            </div>
          </div>
        </div>

        {/* Deterministic Readouts Grid */}
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-800/80">
          <div className="p-3 rounded-xl bg-[#040812] border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">
              Power / Volume (P/V)
            </span>
            <span className="text-lg font-mono font-bold text-cyan-300 sb-tabular">
              {calc.targetPvWm3.toFixed(1)}{" "}
              <span className="text-xs font-normal text-slate-400">W/m³</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#040812] border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">
              Impeller Tip Speed
            </span>
            <span
              className={`text-lg font-mono font-bold sb-tabular ${
                calc.shearStatus === "critical"
                  ? "text-rose-400"
                  : calc.shearStatus === "watch"
                  ? "text-amber-300"
                  : "text-emerald-300"
              }`}
            >
              {calc.targetTipSpeedMs.toFixed(2)}{" "}
              <span className="text-xs font-normal text-slate-400">m/s</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#040812] border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">
              Predicted kLa (Van&apos;t Riet)
            </span>
            <span className="text-lg font-mono font-bold text-emerald-300 sb-tabular">
              {calc.targetKlaPerH.toFixed(1)}{" "}
              <span className="text-xs font-normal text-slate-400">1/h</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#040812] border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">
              Mixing Reynolds (Re)
            </span>
            <span className="text-lg font-mono font-bold text-slate-100 sb-tabular">
              {(calc.targetReynolds / 1000).toFixed(1)}k{" "}
              <span className="text-[10px] font-normal uppercase text-cyan-400">
                {calc.regime}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Right: Animated Scientific Process Curves */}
      <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Card 1: Biomass & Product Titer */}
        <div className="sb-surface rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-start justify-between gap-2 mb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                Biomass &amp; Yield Kinetics (0–120 h)
              </span>
              <h4 className="text-sm font-display font-semibold text-slate-100 mt-0.5">
                DCW &amp; mAb Titer Trajectory
              </h4>
            </div>
            <DataOriginBadge origin="sample" />
          </div>

          <svg viewBox="0 0 340 110" className="w-full h-28 overflow-visible">
            <line x1="0" y1="28" x2="340" y2="28" stroke="rgba(148,163,184,0.1)" strokeDasharray="3 3" />
            <line x1="0" y1="56" x2="340" y2="56" stroke="rgba(148,163,184,0.1)" strokeDasharray="3 3" />
            <line x1="0" y1="84" x2="340" y2="84" stroke="rgba(148,163,184,0.1)" strokeDasharray="3 3" />
            <path
              d={biomassPath}
              fill="none"
              stroke="#34D399"
              strokeWidth="2.2"
            />
            <path
              d={titerPath}
              fill="none"
              stroke="#22D3EE"
              strokeWidth="2.2"
              strokeDasharray="5 3"
            />
          </svg>

          <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-[11px] font-mono">
            <span className="text-emerald-300">● Peak Biomass: 17.3 g/L</span>
            <span className="text-cyan-300">--- Harvest Titer: 4.62 g/L</span>
          </div>
        </div>

        {/* Card 2: Dissolved Oxygen & Glucose */}
        <div className="sb-surface rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-start justify-between gap-2 mb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                Metabolic &amp; Mass Transfer Balance
              </span>
              <h4 className="text-sm font-display font-semibold text-slate-100 mt-0.5">
                Dissolved O₂ &amp; Glucose Depletion
              </h4>
            </div>
            <DataOriginBadge origin="sample" />
          </div>

          <svg viewBox="0 0 340 110" className="w-full h-28 overflow-visible">
            <line x1="0" y1="28" x2="340" y2="28" stroke="rgba(148,163,184,0.1)" strokeDasharray="3 3" />
            <line x1="0" y1="56" x2="340" y2="56" stroke="rgba(148,163,184,0.1)" strokeDasharray="3 3" />
            <line x1="0" y1="84" x2="340" y2="84" stroke="rgba(148,163,184,0.1)" strokeDasharray="3 3" />
            <path
              d={doPath}
              fill="none"
              stroke="#38BDF8"
              strokeWidth="2.2"
            />
            <path
              d={glucosePath}
              fill="none"
              stroke="#FBBF24"
              strokeWidth="2"
            />
          </svg>

          <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-[11px] font-mono">
            <span className="text-sky-300">● dO₂ Setpoint: 40.0 %sat</span>
            <span className="text-amber-300">● Residual Glucose: 2.2 g/L</span>
          </div>
        </div>

        {/* Card 3: Controlled Environment Strip */}
        <div className="sm:col-span-2 sb-surface rounded-2xl p-5 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Temperature</span>
            <span className="text-xl font-mono font-bold text-slate-100 sb-tabular">36.8 °C</span>
            <span className="block text-[10px] font-mono text-emerald-400 mt-0.5">±0.1 °C Nominal</span>
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Broth pH</span>
            <span className="text-xl font-mono font-bold text-slate-100 sb-tabular">7.05 pH</span>
            <span className="block text-[10px] font-mono text-emerald-400 mt-0.5">Deadband ±0.05</span>
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Process Efficiency</span>
            <span className="text-xl font-mono font-bold text-cyan-300 sb-tabular">94.2 %</span>
            <span className="block text-[10px] font-mono text-slate-400 mt-0.5">OTR / OUR Ratio</span>
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Shear Margin</span>
            <span className="text-xl font-mono font-bold text-emerald-300 sb-tabular">
              {Math.max(0, 2.2 - calc.targetTipSpeedMs).toFixed(2)} m/s
            </span>
            <span className="block text-[10px] font-mono text-slate-400 mt-0.5">Below 2.2 m/s Limit</span>
          </div>
        </div>
      </div>
    </div>
  );
}
