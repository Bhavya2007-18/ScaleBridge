"use client";

import React from "react";
import { CANONICAL_VARIABLES } from "../lib/format";

export interface UnitSelectProps {
  value: string;
  variableKey?: string;
  category?:
    | "volume"
    | "speed"
    | "power"
    | "flow"
    | "kla"
    | "temperature"
    | "concentration"
    | "pressure"
    | "rate"
    | "dimensionless";
  onChange: (val: string) => void;
  className?: string;
}

const UNITS_BY_CATEGORY: Record<string, string[]> = {
  volume: ["L", "mL", "m^3"],
  speed: ["rpm", "1/s", "1/min", "m/s"],
  power: ["W", "kW", "W/m^3"],
  flow: ["L/min", "SLPM", "m^3/h", "m^3/s", "mL/h", "vvm"],
  kla: ["1/h", "1/s"],
  temperature: ["degC", "K", "degF"],
  concentration: ["g/L", "kg/m^3", "mmol/L", "mg/L", "U/mL"],
  pressure: ["bar(a)", "kPa", "Pa", "psi"],
  rate: ["mmol/(L*h)", "mol/(m^3*s)"],
  dimensionless: ["pH", "percent_air_saturation", "% air sat", "dimensionless"],
};

export const UnitSelect: React.FC<UnitSelectProps> = ({
  value,
  variableKey,
  category = "volume",
  onChange,
  className = "",
}) => {
  const varSpec = variableKey
    ? CANONICAL_VARIABLES.find((v) => v.key === variableKey)
    : undefined;

  const units = varSpec
    ? [...varSpec.acceptedUnits, ...(varSpec.ambiguousUnits || [])]
    : UNITS_BY_CATEGORY[category] || ["L", "rpm", "W", "degC", "g/L"];

  const isAmbiguous = varSpec?.ambiguousUnits?.includes(value);

  return (
    <div className="inline-flex items-center gap-1.5">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Select physical unit"
        className={`rounded-lg bg-[#09090B] border ${
          isAmbiguous ? "border-amber-400/60 text-amber-300" : "border-[#27272A] text-[#FAFAFA]"
        } px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:border-[#A1A1AA] ${className}`}
      >
        <option value="">-- Unit --</option>
        {units.map((u) => (
          <option key={u} value={u} className="bg-[#111114] text-[#FAFAFA]">
            {u}
          </option>
        ))}
      </select>
      {isAmbiguous && (
        <span
          className="text-[10px] font-mono text-amber-300 px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-400/30"
          title="Ambiguous unit (DQ-UNIT-AMBIGUOUS): select explicit basis (e.g., percent_air_saturation or bar(a))"
        >
          DQ-UNIT-AMBIGUOUS
        </span>
      )}
    </div>
  );
};
