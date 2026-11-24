/**
 * Scientific formatting, unit normalization, and client-side CSV/data-quality utilities
 * owned by Person 3 (Frontend Core, Vessel Management & Data Ingestion Workflows).
 */

export interface CanonicalVariableSpec {
  key: string;
  label: string;
  category:
    | "dimensionless"
    | "do_sat"
    | "concentration"
    | "temperature"
    | "rotation"
    | "flow"
    | "pressure"
    | "volume"
    | "rate"
    | "power";
  siUnit: string;
  displayUnit: string;
  acceptedUnits: string[];
  ambiguousUnits?: string[];
  requiresCalibration?: boolean;
}

export const CANONICAL_VARIABLES: CanonicalVariableSpec[] = [
  {
    key: "ph",
    label: "Broth pH",
    category: "dimensionless",
    siUnit: "pH",
    displayUnit: "pH",
    acceptedUnits: ["pH", "dimensionless"],
    requiresCalibration: true,
  },
  {
    key: "dissolved_oxygen",
    label: "Dissolved Oxygen (% air sat)",
    category: "do_sat",
    siUnit: "percent_air_saturation",
    displayUnit: "% air sat",
    acceptedUnits: ["percent_air_saturation", "% air sat", "%sat", "%DO"],
    ambiguousUnits: ["%"],
    requiresCalibration: true,
  },
  {
    key: "temperature",
    label: "Broth Temperature",
    category: "temperature",
    siUnit: "K",
    displayUnit: "degC",
    acceptedUnits: ["degC", "°C", "K", "degF"],
  },
  {
    key: "agitation_speed",
    label: "Agitation Speed (N)",
    category: "rotation",
    siUnit: "1/s",
    displayUnit: "rpm",
    acceptedUnits: ["rpm", "1/min", "1/s", "rps"],
  },
  {
    key: "airflow",
    label: "Sparger Airflow (Q_g)",
    category: "flow",
    siUnit: "m^3/s",
    displayUnit: "L/min",
    acceptedUnits: ["L/min", "SLPM", "m^3/h", "m^3/s", "mL/min"],
  },
  {
    key: "oxygen_flow",
    label: "Pure O₂ Supplementation Flow",
    category: "flow",
    siUnit: "m^3/s",
    displayUnit: "L/min",
    acceptedUnits: ["L/min", "SLPM", "m^3/h", "m^3/s", "mL/min"],
  },
  {
    key: "working_volume",
    label: "Working Liquid Volume (V)",
    category: "volume",
    siUnit: "m^3",
    displayUnit: "L",
    acceptedUnits: ["L", "mL", "m^3"],
  },
  {
    key: "headspace_pressure",
    label: "Headspace Pressure (Absolute)",
    category: "pressure",
    siUnit: "Pa",
    displayUnit: "bar(a)",
    acceptedUnits: ["bar(a)", "kPa", "Pa", "psi"],
    ambiguousUnits: ["bar", "bar(g)"],
  },
  {
    key: "feed_rate",
    label: "Nutrient Feed Rate",
    category: "flow",
    siUnit: "m^3/s",
    displayUnit: "mL/h",
    acceptedUnits: ["mL/h", "L/h", "g/h"],
  },
  {
    key: "our",
    label: "Oxygen Uptake Rate (OUR)",
    category: "rate",
    siUnit: "mol/(m^3*s)",
    displayUnit: "mmol/(L*h)",
    acceptedUnits: ["mmol/(L*h)", "mol/(m^3*s)", "mmol/L/h"],
  },
  {
    key: "cer",
    label: "CO₂ Evolution Rate (CER)",
    category: "rate",
    siUnit: "mol/(m^3*s)",
    displayUnit: "mmol/(L*h)",
    acceptedUnits: ["mmol/(L*h)", "mol/(m^3*s)", "mmol/L/h"],
  },
  {
    key: "power_draw",
    label: "Measured Agitator Power Draw",
    category: "power",
    siUnit: "W",
    displayUnit: "W",
    acceptedUnits: ["W", "kW"],
  },
  {
    key: "biomass_dcw",
    label: "Dry Cell Weight (Biomass)",
    category: "concentration",
    siUnit: "kg/m^3",
    displayUnit: "g/L",
    acceptedUnits: ["g/L", "kg/m^3", "mg/mL"],
  },
  {
    key: "substrate_glucose",
    label: "Residual Glucose Concentration",
    category: "concentration",
    siUnit: "kg/m^3",
    displayUnit: "g/L",
    acceptedUnits: ["g/L", "kg/m^3", "mmol/L"],
  },
  {
    key: "product_titre",
    label: "Product Titer / Activity",
    category: "concentration",
    siUnit: "kg/m^3",
    displayUnit: "g/L",
    acceptedUnits: ["g/L", "kg/m^3", "mg/L", "U/mL"],
  },
];

export function formatNumber(val?: number | null, decimals: number = 2): string {
  if (val === undefined || val === null || Number.isNaN(val)) return "—";
  return Number(val).toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
}

export function formatDateTime(isoString?: string | null): string {
  if (!isoString) return "—";
  const d = new Date(isoString);
  if (Number.isNaN(d.getTime())) return isoString;
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Deterministic client-side unit conversion mirroring `scalebridge_science.units`.
 * Ensures rotational speed converts `rpm -> 1/s` (revolutions/sec, never radians/sec).
 */
export function convertToSi(value: number, fromUnit: string, variableKey: string): {
  valueSi: number;
  unitSi: string;
  valueDisplay: number;
  unitDisplay: string;
} {
  const spec = CANONICAL_VARIABLES.find((v) => v.key === variableKey);
  const unitSi = spec?.siUnit || fromUnit;
  const unitDisplay = spec?.displayUnit || fromUnit;
  const u = fromUnit.trim();

  // Temperature (offset units)
  if (variableKey === "temperature") {
    let k = value;
    if (u === "degC" || u === "°C") k = value + 273.15;
    else if (u === "degF") k = (value - 32) * (5 / 9) + 273.15;
    const c = k - 273.15;
    return { valueSi: k, unitSi: "K", valueDisplay: c, unitDisplay: "degC" };
  }

  // Rotational speed (rpm -> 1/s revolutions per second, never rad/s)
  if (variableKey === "agitation_speed") {
    let rps = value;
    if (u === "rpm" || u === "1/min") rps = value / 60.0;
    return { valueSi: rps, unitSi: "1/s", valueDisplay: rps * 60.0, unitDisplay: "rpm" };
  }

  // Gas flow (L/min, SLPM, m^3/h -> m^3/s)
  if (variableKey === "airflow" || variableKey === "oxygen_flow") {
    let m3s = value;
    if (u === "L/min" || u === "SLPM") m3s = value / 60000.0;
    else if (u === "mL/min") m3s = value / 60000000.0;
    else if (u === "m^3/h") m3s = value / 3600.0;
    return { valueSi: m3s, unitSi: "m^3/s", valueDisplay: m3s * 60000.0, unitDisplay: "L/min" };
  }

  // Volume (L, mL -> m^3)
  if (variableKey === "working_volume") {
    let m3 = value;
    if (u === "L") m3 = value / 1000.0;
    else if (u === "mL") m3 = value / 1000000.0;
    return { valueSi: m3, unitSi: "m^3", valueDisplay: m3 * 1000.0, unitDisplay: "L" };
  }

  // OUR / CER (mmol/(L*h) -> mol/(m^3*s))
  if (variableKey === "our" || variableKey === "cer") {
    let molM3s = value;
    if (u === "mmol/(L*h)" || u === "mmol/L/h") molM3s = value / 3600.0;
    return {
      valueSi: molM3s,
      unitSi: "mol/(m^3*s)",
      valueDisplay: molM3s * 3600.0,
      unitDisplay: "mmol/(L*h)",
    };
  }

  // Power (kW -> W)
  if (variableKey === "power_draw") {
    const w = u === "kW" ? value * 1000.0 : value;
    return { valueSi: w, unitSi: "W", valueDisplay: w, unitDisplay: "W" };
  }

  return { valueSi: value, unitSi, valueDisplay: value, unitDisplay };
}

export function suggestVariableForHeader(header: string): {
  variable: string;
  unit: string;
} {
  const low = header.toLowerCase();
  if (low.includes("ph")) return { variable: "ph", unit: "pH" };
  if (low.includes("do") || low.includes("dissolved_oxygen") || low.includes("oxygen_sat")) {
    return { variable: "dissolved_oxygen", unit: "percent_air_saturation" };
  }
  if (low.includes("temp")) return { variable: "temperature", unit: "degC" };
  if (low.includes("rpm") || low.includes("agit") || low.includes("stir")) {
    return { variable: "agitation_speed", unit: "rpm" };
  }
  if (low.includes("air") || low.includes("sparg") || low.includes("slpm")) {
    return { variable: "airflow", unit: "L/min" };
  }
  if (low.includes("our")) return { variable: "our", unit: "mmol/(L*h)" };
  if (low.includes("cer")) return { variable: "cer", unit: "mmol/(L*h)" };
  if (low.includes("vol")) return { variable: "working_volume", unit: "L" };
  if (low.includes("feed")) return { variable: "feed_rate", unit: "mL/h" };
  if (low.includes("dcw") || low.includes("biomass")) return { variable: "biomass_dcw", unit: "g/L" };
  if (low.includes("gluc")) return { variable: "substrate_glucose", unit: "g/L" };
  if (low.includes("titer") || low.includes("titre") || low.includes("mab")) {
    return { variable: "product_titre", unit: "g/L" };
  }
  if (low.includes("power")) return { variable: "power_draw", unit: "W" };
  return { variable: "", unit: "" };
}

export const SYNTHETIC_GOLDEN_CSV = `elapsed_h,Temperature [degC],pH,DO [% air sat],Stirrer [rpm],Airflow [L/min],Working_Volume [L],OUR [mmol/(L*h)],Biomass_DCW [g/L],Glucose [g/L],Titer [g/L]
0.0,36.8,7.12,98.2,350,1.2,1.85,4.2,0.45,24.0,0.02
12.0,36.8,7.10,84.5,380,1.4,1.88,11.8,1.35,21.8,0.14
24.0,36.8,7.08,68.4,410,1.6,1.92,24.5,3.40,17.6,0.42
36.0,36.9,7.05,52.0,435,1.8,1.95,38.0,6.80,12.4,0.96
48.0,36.8,7.03,43.2,450,2.0,1.98,46.2,10.90,8.1,1.64
60.0,36.8,7.02,40.5,460,2.1,2.01,51.4,14.20,11.5,2.38
72.0,36.7,7.01,39.8,465,2.1,2.04,53.0,16.40,9.2,3.12
84.0,36.8,7.02,40.1,460,2.0,2.06,49.5,17.30,6.8,3.74
96.0,36.8,7.04,41.6,445,1.9,2.08,43.1,17.10,4.5,4.18
108.0,36.8,7.06,44.0,430,1.8,2.10,36.4,16.60,3.1,4.46
120.0,36.8,7.08,47.5,415,1.7,2.10,29.8,15.90,2.2,4.62`;
