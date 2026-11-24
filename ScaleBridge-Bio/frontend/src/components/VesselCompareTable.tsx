"use client";

import React from "react";
import type { Vessel } from "../api/types";
import type { VesselRecord } from "../lib/api";
import { formatNumber } from "../lib/format";

export type AnyVessel = Vessel | VesselRecord;

export interface VesselCompareTableProps {
  sourceVessel: AnyVessel;
  targetVessel: AnyVessel;
}

interface NormalizedVesselProfile {
  id: string;
  name: string;
  scaleClass: string;
  manufacturer: string;
  workingVolMinL: number | null;
  workingVolMaxL: number;
  tankDiameterM: number | null;
  liquidHeightM: number | null;
  impellerDiameterM: number | null;
  powerNumberNp: number | null;
  impellerType: string;
  impellerCount: number | null;
  spargerType: string;
  maxRpm: number | null;
  maxPowerW: number | null;
  maxGassingVvm: number | null;
  coolingCapacityW: number | null;
  instrumentation: string[];
  controls: string[];
  missingSpecs: string[];
}

function normalizeVessel(v: AnyVessel): NormalizedVesselProfile {
  if ("latest_version" in v) {
    const p = v.latest_version.parameters || {};
    const volMax = p.working_volume_max?.value ?? 2.0;
    const volMin = p.working_volume_min?.value ?? Number((volMax * 0.35).toFixed(2));
    const impD = p.impeller_diameter?.value ?? null;
    // Estimate inner tank diameter T = D / 0.35 when not explicitly provided
    const tankD =
      p.vessel_inner_diameter?.value ??
      (impD ? Number((impD / 0.35).toFixed(3)) : null);
    // Estimate liquid height H_L from cylindrical volume V = (pi/4) * T^2 * H_L
    const volM3 = volMax / 1000.0;
    const liqH =
      p.liquid_height_at_working_volume?.value ??
      (tankD
        ? Number((volM3 / (Math.PI * Math.pow(tankD / 2, 2))).toFixed(3))
        : null);

    return {
      id: v.id,
      name: v.name,
      scaleClass: v.scale_class,
      manufacturer: v.manufacturer || "Custom",
      workingVolMinL: volMin,
      workingVolMaxL: volMax,
      tankDiameterM: tankD,
      liquidHeightM: liqH,
      impellerDiameterM: impD,
      powerNumberNp: p.impeller_power_number?.value ?? 2.4,
      impellerType: v.latest_version.impeller_type || "Standard Turbine",
      impellerCount: v.latest_version.impeller_count,
      spargerType: v.latest_version.sparger_type || "Ring Sparger",
      maxRpm: p.max_agitation_speed?.value ?? p.agitation_speed_max?.value ?? null,
      maxPowerW: p.max_power?.value ?? p.motor_power_limit?.value ?? null,
      maxGassingVvm: p.max_aeration?.value ?? null,
      coolingCapacityW: p.cooling_capacity?.value ?? null,
      instrumentation: v.latest_version.instrumentation || [],
      controls: v.latest_version.controls || [],
      missingSpecs: (v.missing_specifications || []).map((m) => m.key),
    };
  }

  const volMax = v.working_volume_max_l || 2.0;
  const volM3 = volMax / 1000.0;
  const ar = v.aspect_ratio || 2.2;
  const tankD = Math.pow((4 * volM3) / (Math.PI * ar), 1 / 3);
  const impD = tankD * 0.35;
  const liqH = tankD * ar;

  return {
    id: v.id,
    name: v.name,
    scaleClass: v.scale_category,
    manufacturer: v.facility || "Facility Node",
    workingVolMinL: v.working_volume_min_l,
    workingVolMaxL: volMax,
    tankDiameterM: Number(tankD.toFixed(3)),
    liquidHeightM: Number(liqH.toFixed(3)),
    impellerDiameterM: Number(impD.toFixed(3)),
    powerNumberNp: 2.4,
    impellerType: (v.impeller_types || []).join(", ") || "Rushton",
    impellerCount: v.impeller_count,
    spargerType: v.sparger_type || "Ring Sparger",
    maxRpm: v.max_rpm ?? null,
    maxPowerW: v.max_power_w ?? null,
    maxGassingVvm: v.max_gassing_vvm ?? null,
    coolingCapacityW: null,
    instrumentation: ["ph_probe", "do_probe", "temperature_probe"],
    controls: ["do_cascade_agitation", "temperature_control"],
    missingSpecs: [],
  };
}

export const VesselCompareTable: React.FC<VesselCompareTableProps> = ({
  sourceVessel,
  targetVessel,
}) => {
  const src = normalizeVessel(sourceVessel);
  const tgt = normalizeVessel(targetVessel);

  const scaleFactor = tgt.workingVolMaxL / Math.max(0.001, src.workingVolMaxL);
  const srcDOverT =
    src.impellerDiameterM && src.tankDiameterM
      ? src.impellerDiameterM / src.tankDiameterM
      : null;
  const tgtDOverT =
    tgt.impellerDiameterM && tgt.tankDiameterM
      ? tgt.impellerDiameterM / tgt.tankDiameterM
      : null;

  const srcHlOverT =
    src.liquidHeightM && src.tankDiameterM
      ? src.liquidHeightM / src.tankDiameterM
      : null;
  const tgtHlOverT =
    tgt.liquidHeightM && tgt.tankDiameterM
      ? tgt.liquidHeightM / tgt.tankDiameterM
      : null;

  const dOverTDriftPct =
    srcDOverT && tgtDOverT
      ? (Math.abs(tgtDOverT - srcDOverT) / srcDOverT) * 100
      : null;
  const hlOverTDriftPct =
    srcHlOverT && tgtHlOverT
      ? (Math.abs(tgtHlOverT - srcHlOverT) / srcHlOverT) * 100
      : null;

  const impellerMismatch =
    src.impellerType.toLowerCase() !== tgt.impellerType.toLowerCase() ||
    src.impellerCount !== tgt.impellerCount;

  const missingInTarget = src.instrumentation.filter(
    (inst) => !tgt.instrumentation.includes(inst)
  );

  return (
    <div className="overflow-hidden border border-[#27272A] rounded-[12px] bg-[#111114] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]">
      <div className="p-4 border-b border-[#27272A] flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
          <span className="text-[#FAFAFA] font-semibold">
            Side-by-Side Vessel Geometry &amp; Capability Envelope Matrix
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="px-2.5 py-1 rounded-md bg-[#09090B] border border-[#27272A] text-[#FAFAFA]">
            SCALE FACTOR: {formatNumber(scaleFactor, 1)}×
          </span>
          {impellerMismatch && (
            <span className="px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-400/25 text-amber-300">
              R-MIX-004: GEOMETRIC NON-SIMILARITY
            </span>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#09090B] text-[#71717A] border-b border-[#27272A] font-sans text-[11px] font-medium">
            <tr>
              <th className="p-3.5">Engineering Parameter / Ratio</th>
              <th className="p-3.5">Source ({src.name})</th>
              <th className="p-3.5">Target ({tgt.name})</th>
              <th className="p-3.5">Scale-Up Transformation &amp; Check</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#18181B] text-[#A1A1AA]">
            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Scale Classification &amp; Vendor
              </td>
              <td className="p-3.5 uppercase">
                {src.scaleClass} · {src.manufacturer}
              </td>
              <td className="p-3.5 uppercase text-[#FAFAFA]">
                {tgt.scaleClass} · {tgt.manufacturer}
              </td>
              <td className="p-3.5 text-[#71717A]">
                {src.scaleClass.toUpperCase()} → {tgt.scaleClass.toUpperCase()} Transfer
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Working Volume Envelope (C-VOLUME-RANGE)
              </td>
              <td className="p-3.5 sb-tabular">
                {formatNumber(src.workingVolMinL, 1)} – {formatNumber(src.workingVolMaxL, 1)} L
              </td>
              <td className="p-3.5 sb-tabular text-[#10B981] font-semibold">
                {formatNumber(tgt.workingVolMinL, 1)} – {formatNumber(tgt.workingVolMaxL, 1)} L
              </td>
              <td className="p-3.5 text-[#FAFAFA] sb-tabular">
                {formatNumber(scaleFactor, 1)}× Volumetric Expansion
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Impeller Diameter D &amp; Inner Tank Diameter T
              </td>
              <td className="p-3.5 sb-tabular">
                D = {formatNumber(src.impellerDiameterM, 3)} m · T ={" "}
                {formatNumber(src.tankDiameterM, 3)} m
              </td>
              <td className="p-3.5 sb-tabular">
                D = {formatNumber(tgt.impellerDiameterM, 3)} m · T ={" "}
                {formatNumber(tgt.tankDiameterM, 3)} m
              </td>
              <td className="p-3.5 text-[#71717A] sb-tabular">
                Linear Scale Ratio:{" "}
                {src.impellerDiameterM && tgt.impellerDiameterM
                  ? `${formatNumber(tgt.impellerDiameterM / src.impellerDiameterM, 2)}×`
                  : "—"}
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Impeller-to-Tank Ratio D/T (F-GEO-001)
              </td>
              <td className="p-3.5 sb-tabular">{formatNumber(srcDOverT, 3)}</td>
              <td className="p-3.5 sb-tabular">{formatNumber(tgtDOverT, 3)}</td>
              <td className="p-3.5 sb-tabular">
                {dOverTDriftPct !== null ? (
                  <span
                    className={
                      dOverTDriftPct > 15 ? "text-amber-300" : "text-[#10B981]"
                    }
                  >
                    Δ(D/T) = {formatNumber(dOverTDriftPct, 1)}%{" "}
                    {dOverTDriftPct > 15 ? "(R-MIX-004 Drift)" : "(Similar)"}
                  </span>
                ) : (
                  "Insufficient geometry"
                )}
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Liquid Aspect Ratio H_L/T (F-GEO-002)
              </td>
              <td className="p-3.5 sb-tabular">{formatNumber(srcHlOverT, 2)}</td>
              <td className="p-3.5 sb-tabular">{formatNumber(tgtHlOverT, 2)}</td>
              <td className="p-3.5 sb-tabular">
                {hlOverTDriftPct !== null ? (
                  <span
                    className={
                      hlOverTDriftPct > 20 ? "text-amber-300" : "text-[#10B981]"
                    }
                  >
                    Δ(H_L/T) = {formatNumber(hlOverTDriftPct, 1)}%
                  </span>
                ) : (
                  "Insufficient geometry"
                )}
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Impeller &amp; Sparger Architecture
              </td>
              <td className="p-3.5">
                {src.impellerCount ?? 1}× {src.impellerType} · {src.spargerType}
              </td>
              <td className="p-3.5">
                {tgt.impellerCount ?? 1}× {tgt.impellerType} · {tgt.spargerType}
              </td>
              <td className="p-3.5">
                {impellerMismatch ? (
                  <span className="text-amber-300">
                    Impeller type/stage count differs → VT-REVIEW-GEOMETRY
                  </span>
                ) : (
                  <span className="text-[#10B981]">Geometrically matched</span>
                )}
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Agitation Speed Ceiling (C-AGIT-RANGE)
              </td>
              <td className="p-3.5 sb-tabular">{formatNumber(src.maxRpm, 0)} rpm</td>
              <td className="p-3.5 sb-tabular">{formatNumber(tgt.maxRpm, 0)} rpm</td>
              <td className="p-3.5 text-[#71717A]">
                Larger radius D requires lower RPM for constant P/V or u_tip
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Rated Motor Shaft Power (C-MOTOR-POWER)
              </td>
              <td className="p-3.5 sb-tabular">{formatNumber(src.maxPowerW, 0)} W</td>
              <td className="p-3.5 sb-tabular text-[#FAFAFA]">
                {formatNumber(tgt.maxPowerW, 0)} W
              </td>
              <td className="p-3.5 sb-tabular text-[#A1A1AA]">
                Max Specific Power:{" "}
                {tgt.maxPowerW
                  ? `${formatNumber(tgt.maxPowerW / (tgt.workingVolMaxL / 1000), 0)} W/m³`
                  : "—"}
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Aeration Capacity Ceiling (C-GAS-RANGE)
              </td>
              <td className="p-3.5 sb-tabular">{formatNumber(src.maxGassingVvm, 2)} vvm</td>
              <td className="p-3.5 sb-tabular">{formatNumber(tgt.maxGassingVvm, 2)} vvm</td>
              <td className="p-3.5 text-[#71717A]">
                Superficial gas velocity v_s scales with liquid height H_L
              </td>
            </tr>

            <tr className="hover:bg-[#16161A]">
              <td className="p-3.5 text-[#FAFAFA] font-sans font-medium">
                Instrumentation &amp; Control Parity (C-INSTRUMENT)
              </td>
              <td className="p-3.5 text-[11px]">{src.instrumentation.join(", ") || "—"}</td>
              <td className="p-3.5 text-[11px]">{tgt.instrumentation.join(", ") || "—"}</td>
              <td className="p-3.5">
                {missingInTarget.length > 0 ? (
                  <span className="text-amber-300">
                    Missing on Target: {missingInTarget.join(", ")}
                  </span>
                ) : (
                  <span className="text-[#10B981]">All source sensors available</span>
                )}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {(src.missingSpecs.length > 0 || tgt.missingSpecs.length > 0) && (
        <div className="p-3.5 bg-amber-500/10 border-t border-amber-400/25 text-xs font-mono text-amber-200 flex flex-wrap items-center justify-between gap-2">
          <div>
            <strong>[R-EQP-006 / Missing Specifications]:</strong>{" "}
            {tgt.missingSpecs.length > 0 &&
              `Target (${tgt.name}) missing: ${tgt.missingSpecs.join(", ")}. `}
            {src.missingSpecs.length > 0 &&
              `Source (${src.name}) missing: ${src.missingSpecs.join(", ")}.`}
          </div>
          <span className="text-[10px] uppercase px-2 py-0.5 rounded bg-amber-500/20 border border-amber-400/40">
            Triggers VT-DATA-VESSEL-SPEC
          </span>
        </div>
      )}
    </div>
  );
};
