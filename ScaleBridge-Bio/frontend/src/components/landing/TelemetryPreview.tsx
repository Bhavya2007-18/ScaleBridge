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
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
      {/* Left: Interactive Digital Twin Parameter Sliders & Deterministic Readouts */}
      <div className="lg:col-span-5 sb-surface rounded-[12px] p-6 flex flex-col justify-between space-y-6">
        <div>
          <div className="flex items-center justify-between gap-2 mb-4">
            <span className="text-[12px] font-semibold text-[#10B981]">
              Live Hydrodynamic Coupling
            </span>
            <DataOriginBadge origin="simulated" />
          </div>
          <h3 className="text-[16px] font-semibold leading-[1.4] text-[#FAFAFA]">
            Tune Operating Parameters on the Digital Twin
          </h3>
          <p className="mt-1.5 text-[14px] text-[#A1A1AA] leading-[1.6]">
            Adjust pilot vessel agitation and aeration sparging below. The 3D reactor impeller, liquid vortex, and bubble dynamics update in real time alongside deterministic physics.
          </p>
        </div>

        <div className="space-y-5">
          <div>
            <div className="flex justify-between text-[13px] mb-2">
              <span className="text-[#A1A1AA]">Agitation Speed (N)</span>
              <span className="font-mono text-[#FAFAFA] font-medium sb-tabular">
                {rpm} <span className="text-[#71717A] font-normal">rpm</span>
              </span>
            </div>
            <input
              type="range"
              min={60}
              max={240}
              step={5}
              value={rpm}
              onChange={(e) => onRpmChange(Number(e.target.value))}
              className="w-full accent-[#FAFAFA] cursor-pointer"
            />
            <div className="flex justify-between text-[11px] font-mono text-[#71717A] mt-1">
              <span>60 rpm</span>
              <span>240 rpm</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-[13px] mb-2">
              <span className="text-[#A1A1AA]">Aeration Flow Rate (VVM)</span>
              <span className="font-mono text-[#FAFAFA] font-medium sb-tabular">
                {aerationVvm.toFixed(2)} <span className="text-[#71717A] font-normal">vvm</span>
              </span>
            </div>
            <input
              type="range"
              min={0.15}
              max={1.2}
              step={0.05}
              value={aerationVvm}
              onChange={(e) => onAerationChange(Number(e.target.value))}
              className="w-full accent-[#10B981] cursor-pointer"
            />
            <div className="flex justify-between text-[11px] font-mono text-[#71717A] mt-1">
              <span>0.15 vvm</span>
              <span>1.20 vvm</span>
            </div>
          </div>
        </div>

        {/* Deterministic Readouts Grid */}
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-[#27272A]">
          <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
            <span className="text-[11px] font-medium text-[#71717A] block">
              Power / Volume (P/V)
            </span>
            <span className="text-[17px] font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
              {calc.targetPvWm3.toFixed(1)}{" "}
              <span className="text-[11px] font-mono font-normal text-[#71717A]">W/m³</span>
            </span>
          </div>

          <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
            <span className="text-[11px] font-medium text-[#71717A] block">
              Impeller Tip Speed
            </span>
            <span
              className={`text-[17px] font-semibold sb-tabular mt-0.5 inline-block ${
                calc.shearStatus === "critical"
                  ? "text-rose-400"
                  : calc.shearStatus === "watch"
                  ? "text-amber-300"
                  : "text-[#FAFAFA]"
              }`}
            >
              {calc.targetTipSpeedMs.toFixed(2)}{" "}
              <span className="text-[11px] font-mono font-normal text-[#71717A]">m/s</span>
            </span>
          </div>

          <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
            <span className="text-[11px] font-medium text-[#71717A] block">
              Predicted kLa
            </span>
            <span className="text-[17px] font-semibold text-[#10B981] sb-tabular mt-0.5 inline-block">
              {calc.targetKlaPerH.toFixed(1)}{" "}
              <span className="text-[11px] font-mono font-normal text-[#71717A]">1/h</span>
            </span>
          </div>

          <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
            <span className="text-[11px] font-medium text-[#71717A] block">
              Reynolds Number (Re)
            </span>
            <span className="text-[17px] font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
              {(calc.targetReynolds / 1000).toFixed(1)}k{" "}
              <span className="text-[11px] font-normal capitalize text-[#71717A]">
                {calc.regime}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Right: Scientific Process Curves */}
      <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Card 1: Biomass & Product Titer */}
        <div className="sb-surface rounded-[12px] p-6 flex flex-col justify-between">
          <div className="flex items-start justify-between gap-2 mb-4">
            <div>
              <span className="text-[11px] font-medium text-[#71717A] block">
                Biomass &amp; Yield Kinetics (0–120 h)
              </span>
              <h4 className="text-[16px] font-semibold text-[#FAFAFA] leading-[1.4] mt-0.5">
                DCW &amp; mAb Titer Trajectory
              </h4>
            </div>
            <DataOriginBadge origin="sample" />
          </div>

          <svg viewBox="0 0 340 110" className="w-full h-28 overflow-visible">
            <line x1="0" y1="28" x2="340" y2="28" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <line x1="0" y1="56" x2="340" y2="56" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <line x1="0" y1="84" x2="340" y2="84" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <path
              d={biomassPath}
              fill="none"
              stroke="#10B981"
              strokeWidth="2"
            />
            <path
              d={titerPath}
              fill="none"
              stroke="#E4E4E7"
              strokeWidth="1.8"
              strokeDasharray="5 3"
            />
          </svg>

          <div className="flex items-center justify-between pt-3 border-t border-[#27272A] text-[12px]">
            <span className="text-[#10B981]">
              ● Peak Biomass: <span className="font-mono">17.3 g/L</span>
            </span>
            <span className="text-[#A1A1AA]">
              --- Harvest Titer: <span className="font-mono text-[#FAFAFA]">4.62 g/L</span>
            </span>
          </div>
        </div>

        {/* Card 2: Dissolved Oxygen & Glucose */}
        <div className="sb-surface rounded-[12px] p-6 flex flex-col justify-between">
          <div className="flex items-start justify-between gap-2 mb-4">
            <div>
              <span className="text-[11px] font-medium text-[#71717A] block">
                Metabolic &amp; Mass Transfer Balance
              </span>
              <h4 className="text-[16px] font-semibold text-[#FAFAFA] leading-[1.4] mt-0.5">
                Dissolved O₂ &amp; Glucose Depletion
              </h4>
            </div>
            <DataOriginBadge origin="sample" />
          </div>

          <svg viewBox="0 0 340 110" className="w-full h-28 overflow-visible">
            <line x1="0" y1="28" x2="340" y2="28" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <line x1="0" y1="56" x2="340" y2="56" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <line x1="0" y1="84" x2="340" y2="84" stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <path
              d={doPath}
              fill="none"
              stroke="#E4E4E7"
              strokeWidth="2"
            />
            <path
              d={glucosePath}
              fill="none"
              stroke="#F59E0B"
              strokeWidth="1.8"
            />
          </svg>

          <div className="flex items-center justify-between pt-3 border-t border-[#27272A] text-[12px]">
            <span className="text-[#FAFAFA]">
              ● dO₂ Setpoint: <span className="font-mono">40.0 %sat</span>
            </span>
            <span className="text-[#A1A1AA]">
              ● Glucose: <span className="font-mono text-[#FAFAFA]">2.2 g/L</span>
            </span>
          </div>
        </div>

        {/* Card 3: Controlled Environment Strip */}
        <div className="sm:col-span-2 sb-surface rounded-[12px] p-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <span className="text-[12px] text-[#71717A] block">Temperature</span>
            <span className="text-[18px] font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
              36.8 <span className="text-[12px] font-mono font-normal text-[#71717A]">°C</span>
            </span>
            <span className="block text-[11px] font-mono text-[#10B981] mt-0.5">±0.1 °C Nominal</span>
          </div>
          <div>
            <span className="text-[12px] text-[#71717A] block">Broth pH</span>
            <span className="text-[18px] font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
              7.05 <span className="text-[12px] font-mono font-normal text-[#71717A]">pH</span>
            </span>
            <span className="block text-[11px] font-mono text-[#10B981] mt-0.5">Deadband ±0.05</span>
          </div>
          <div>
            <span className="text-[12px] text-[#71717A] block">Process Efficiency</span>
            <span className="text-[18px] font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
              94.2 <span className="text-[12px] font-mono font-normal text-[#71717A]">%</span>
            </span>
            <span className="block text-[11px] text-[#71717A] mt-0.5">OTR / OUR Ratio</span>
          </div>
          <div>
            <span className="text-[12px] text-[#71717A] block">Shear Margin</span>
            <span className="text-[18px] font-semibold text-[#10B981] sb-tabular mt-0.5 inline-block">
              {Math.max(0, 2.2 - calc.targetTipSpeedMs).toFixed(2)}{" "}
              <span className="text-[12px] font-mono font-normal text-[#71717A]">m/s</span>
            </span>
            <span className="block text-[11px] text-[#71717A] mt-0.5">Below 2.2 m/s limit</span>
          </div>
        </div>
      </div>
    </div>
  );
}
