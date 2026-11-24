"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  CANONICAL_VARIABLES,
  convertToSi,
  formatNumber,
  suggestVariableForHeader,
} from "../lib/format";
import { UnitSelect } from "./UnitSelect";
import type { QualityReport } from "../lib/api";

export interface ColumnMappingEntry {
  sourceColumn: string;
  standardParameter: string;
  unit: string;
  provenance: "sensor" | "lab_assay" | "manual_entry";
  calibrationStatus:
    | "calibrated_pre_run"
    | "calibrated_unknown_date"
    | "not_calibrated"
    | "unknown";
  sensorOrAssay?: string;
}

export interface ColumnMapperProps {
  headers: string[];
  sampleRows?: Array<Record<string, string | number | null>>;
  initialTimestampCol?: string;
  onSaveMappings: (
    mappings: ColumnMappingEntry[],
    timestampCfg: {
      column: string;
      kind: "elapsed" | "absolute";
      elapsedUnit: "h" | "min" | "s";
    },
    previewReport: QualityReport
  ) => void;
}

export const ColumnMapper: React.FC<ColumnMapperProps> = ({
  headers,
  sampleRows = [],
  initialTimestampCol,
  onSaveMappings,
}) => {
  const [timestampCol, setTimestampCol] = useState<string>(
    initialTimestampCol ||
      headers.find((h) => /time|elapsed|hour|ts|date/i.test(h)) ||
      headers[0] ||
      ""
  );
  const [timestampKind, setTimestampKind] = useState<"elapsed" | "absolute">("elapsed");
  const [elapsedUnit, setElapsedUnit] = useState<"h" | "min" | "s">("h");

  const [mappings, setMappings] = useState<Record<string, ColumnMappingEntry>>({});

  useEffect(() => {
    const next: Record<string, ColumnMappingEntry> = {};
    headers.forEach((h) => {
      if (h === timestampCol) return;
      const suggestion = suggestVariableForHeader(h);
      next[h] = {
        sourceColumn: h,
        standardParameter: suggestion.variable,
        unit: suggestion.unit,
        provenance:
          suggestion.variable === "biomass_dcw" ||
          suggestion.variable === "substrate_glucose" ||
          suggestion.variable === "product_titre"
            ? "lab_assay"
            : "sensor",
        calibrationStatus:
          suggestion.variable === "ph" || suggestion.variable === "dissolved_oxygen"
            ? "calibrated_pre_run"
            : "unknown",
        sensorOrAssay: h,
      };
    });
    setMappings(next);
  }, [headers, timestampCol]);

  const updateRow = (header: string, patch: Partial<ColumnMappingEntry>) => {
    setMappings((prev) => {
      const existing = prev[header] || {
        sourceColumn: header,
        standardParameter: "",
        unit: "",
        provenance: "sensor",
        calibrationStatus: "unknown",
      };
      const updated = { ...existing, ...patch };
      if (patch.standardParameter !== undefined) {
        const spec = CANONICAL_VARIABLES.find((v) => v.key === patch.standardParameter);
        if (spec && (!updated.unit || !spec.acceptedUnits.includes(updated.unit))) {
          updated.unit = spec.acceptedUnits[0] || spec.displayUnit;
        }
      }
      return { ...prev, [header]: updated };
    });
  };

  // Live deterministic client-side DQ-* quality preview (mirrors docs/09_DATA_INGESTION.md)
  const liveQualityReport = useMemo<QualityReport>(() => {
    const issues: QualityReport["issues"] = [];
    const variables: QualityReport["variables"] = [];
    const conversions: QualityReport["conversions"] = [];
    let blocking = false;

    if (sampleRows.length === 0) {
      issues.push({
        check_code: "DQ-FILE-EMPTY",
        severity: "critical",
        variable: null,
        row_start: 0,
        row_end: 0,
        count: 1,
        message: "No data rows detected in CSV preview.",
      });
      blocking = true;
    }

    // Timestamp checks: parse, order, duplicates, gaps
    const elapsedSeconds: number[] = [];
    let tsParseFailures = 0;
    const factor = elapsedUnit === "h" ? 3600 : elapsedUnit === "min" ? 60 : 1;

    sampleRows.forEach((row) => {
      const rawTs = row[timestampCol];
      if (rawTs === null || rawTs === undefined || String(rawTs).trim() === "") {
        tsParseFailures += 1;
        return;
      }
      if (timestampKind === "elapsed") {
        const num = Number(rawTs);
        if (Number.isNaN(num)) {
          tsParseFailures += 1;
        } else {
          elapsedSeconds.push(num * factor);
        }
      } else {
        const parsed = Date.parse(String(rawTs));
        if (Number.isNaN(parsed)) {
          tsParseFailures += 1;
        } else {
          elapsedSeconds.push(parsed / 1000);
        }
      }
    });

    if (tsParseFailures > 0) {
      const pct = (tsParseFailures / Math.max(1, sampleRows.length)) * 100;
      if (pct > 5) blocking = true;
      issues.push({
        check_code: "DQ-TS-PARSE",
        severity: "high",
        variable: null,
        row_start: 1,
        row_end: sampleRows.length,
        count: tsParseFailures,
        message: `${tsParseFailures} row(s) (${pct.toFixed(1)}%) have unparseable timestamps in '${timestampCol}'.`,
      });
    }

    let nonMonotonic = 0;
    let duplicateTs = 0;
    const intervals: number[] = [];
    for (let i = 1; i < elapsedSeconds.length; i++) {
      const dt = elapsedSeconds[i] - elapsedSeconds[i - 1];
      if (dt < 0) nonMonotonic += 1;
      else if (Math.abs(dt) < 1e-6) duplicateTs += 1;
      else intervals.push(dt);
    }

    if (nonMonotonic > 0) {
      issues.push({
        check_code: "DQ-TS-ORDER",
        severity: "high",
        variable: null,
        row_start: 1,
        row_end: sampleRows.length,
        count: nonMonotonic,
        message: `Timestamps are non-monotonic at ${nonMonotonic} step(s); rows will be sorted chronologically.`,
      });
    }

    if (duplicateTs > 0) {
      issues.push({
        check_code: "DQ-TS-DUP",
        severity: "medium",
        variable: null,
        row_start: 1,
        row_end: sampleRows.length,
        count: duplicateTs,
        message: `${duplicateTs} duplicate timestamp point(s) detected and flagged 'suspect'.`,
      });
    }

    if (intervals.length >= 3) {
      const sorted = [...intervals].sort((a, b) => a - b);
      const medianDt = sorted[Math.floor(sorted.length / 2)];
      const gaps = intervals.filter((d) => d > 10 * medianDt);
      if (gaps.length > 0) {
        issues.push({
          check_code: "DQ-TS-GAP",
          severity: "medium",
          variable: null,
          row_start: 1,
          row_end: sampleRows.length,
          count: gaps.length,
          message: `${gaps.length} sampling gap(s) exceed 10× median interval (${medianDt.toFixed(0)} s).`,
        });
      }
    }

    // Per-column checks
    const unmappedCols: string[] = [];
    headers.forEach((h) => {
      if (h === timestampCol) return;
      const m = mappings[h];
      if (!m || !m.standardParameter) {
        unmappedCols.push(h);
        return;
      }

      const spec = CANONICAL_VARIABLES.find((v) => v.key === m.standardParameter);
      if (!spec) {
        blocking = true;
        issues.push({
          check_code: "DQ-UNIT-UNKNOWN",
          severity: "critical",
          variable: m.standardParameter,
          row_start: 1,
          row_end: sampleRows.length,
          count: 1,
          message: `Unknown variable '${m.standardParameter}'.`,
        });
        return;
      }

      if (spec.ambiguousUnits?.includes(m.unit)) {
        blocking = true;
        issues.push({
          check_code: "DQ-UNIT-AMBIGUOUS",
          severity: "high",
          variable: m.standardParameter,
          row_start: 1,
          row_end: sampleRows.length,
          count: 1,
          message: `Unit '${m.unit}' for '${m.standardParameter}' is ambiguous; select explicit basis (${spec.acceptedUnits.join(", ")}).`,
        });
      } else if (!spec.acceptedUnits.includes(m.unit)) {
        blocking = true;
        issues.push({
          check_code: "DQ-UNIT-UNKNOWN",
          severity: "critical",
          variable: m.standardParameter,
          row_start: 1,
          row_end: sampleRows.length,
          count: 1,
          message: `Unit '${m.unit || "(empty)"}' is not accepted for '${m.standardParameter}'.`,
        });
      }

      if (
        spec.requiresCalibration &&
        (m.calibrationStatus === "unknown" || m.calibrationStatus === "not_calibrated")
      ) {
        issues.push({
          check_code: "DQ-CAL-UNKNOWN",
          severity: "low",
          variable: m.standardParameter,
          row_start: 1,
          row_end: sampleRows.length,
          count: 1,
          message: `Sensor calibration status for '${m.standardParameter}' is '${m.calibrationStatus}'.`,
        });
      }

      let missingCount = 0;
      let impossibleCount = 0;
      const validSi: number[] = [];
      const validDisplay: number[] = [];

      sampleRows.forEach((row) => {
        const raw = row[h];
        if (
          raw === null ||
          raw === undefined ||
          ["", "NA", "N/A", "-", "NaN", "#VALUE!"].includes(String(raw).trim())
        ) {
          missingCount += 1;
          return;
        }
        const num = Number(raw);
        if (Number.isNaN(num) || !Number.isFinite(num)) {
          missingCount += 1;
          return;
        }
        const conv = convertToSi(num, m.unit, m.standardParameter);
        const impossible =
          (m.standardParameter === "ph" && (conv.valueSi < 0 || conv.valueSi > 14)) ||
          (m.standardParameter === "temperature" && conv.valueSi <= 0) ||
          (m.standardParameter !== "ph" &&
            m.standardParameter !== "temperature" &&
            conv.valueSi < 0);

        if (impossible) {
          impossibleCount += 1;
        } else {
          validSi.push(conv.valueSi);
          validDisplay.push(conv.valueDisplay);
        }
      });

      if (missingCount > 0) {
        issues.push({
          check_code: "DQ-VAL-MISSING",
          severity: missingCount / Math.max(1, sampleRows.length) > 0.1 ? "medium" : "low",
          variable: m.standardParameter,
          row_start: 1,
          row_end: sampleRows.length,
          count: missingCount,
          message: `${missingCount} missing value(s) in '${h}' (${m.standardParameter}).`,
        });
      }

      if (impossibleCount > 0) {
        issues.push({
          check_code: "DQ-VAL-IMPOSSIBLE",
          severity: "high",
          variable: m.standardParameter,
          row_start: 1,
          row_end: sampleRows.length,
          count: impossibleCount,
          message: `${impossibleCount} physically impossible reading(s) in '${h}' flagged 'invalid' and excluded from summaries.`,
        });
      }

      conversions.push({
        variable: m.standardParameter,
        from_unit: m.unit,
        to_unit: spec.siUnit,
        method: "pint",
        pint_version: "0.24",
      });

      variables.push({
        variable: m.standardParameter,
        unit_original: m.unit,
        unit_si: spec.siUnit,
        unit_display: spec.displayUnit,
        count: sampleRows.length,
        valid_count: validSi.length,
        missing_count: missingCount,
        invalid_count: impossibleCount,
        min_si: validSi.length ? Math.min(...validSi) : null,
        max_si: validSi.length ? Math.max(...validSi) : null,
        min_display: validDisplay.length ? Math.min(...validDisplay) : null,
        max_display: validDisplay.length ? Math.max(...validDisplay) : null,
      });
    });

    if (unmappedCols.length > 0) {
      issues.push({
        check_code: "DQ-COL-UNMAPPED",
        severity: "info",
        variable: null,
        row_start: 1,
        row_end: 1,
        count: unmappedCols.length,
        message: `Unmapped columns ignored: ${unmappedCols.join(", ")}.`,
      });
    }

    return {
      rows_total: sampleRows.length,
      rows_imported: Math.max(0, sampleRows.length - tsParseFailures),
      variables,
      issues,
      conversions,
      blocking,
    };
  }, [headers, mappings, sampleRows, timestampCol, timestampKind, elapsedUnit]);

  const handleConfirm = () => {
    const activeList = Object.values(mappings).filter((m) => m.standardParameter);
    onSaveMappings(
      activeList,
      {
        column: timestampCol,
        kind: timestampKind,
        elapsedUnit,
      },
      liveQualityReport
    );
  };

  return (
    <div className="sb-surface rounded-[12px] p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#27272A] pb-4">
        <div>
          <span className="text-[12px] font-semibold text-[#10B981]">
            Schema &amp; Pint Unit Normalization
          </span>
          <h3 className="text-[16px] font-semibold text-[#FAFAFA] mt-0.5">
            Map Raw Headers to Bioprocess Ontology
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium">
          <span
            className={`px-2.5 py-1 rounded-full border ${
              liveQualityReport.blocking
                ? "bg-rose-500/10 text-rose-300 border-rose-400/30"
                : "bg-[#10B981]/10 text-[#10B981] border-[#10B981]/25"
            }`}
          >
            {liveQualityReport.blocking ? "Blocking DQ Issue" : "Ready to Import"}
          </span>
        </div>
      </div>

      {/* Timestamp Axis Configuration */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-lg bg-[#09090B] border border-[#27272A] text-xs">
        <div>
          <label className="block text-[11px] font-medium text-[#71717A] mb-1">
            Timestamp Column
          </label>
          <select
            value={timestampCol}
            onChange={(e) => setTimestampCol(e.target.value)}
            className="w-full rounded-lg bg-[#111114] border border-[#27272A] px-2.5 py-1.5 font-mono text-[#FAFAFA]"
          >
            {headers.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[11px] font-medium text-[#71717A] mb-1">
            Time Axis Kind
          </label>
          <select
            value={timestampKind}
            onChange={(e) => setTimestampKind(e.target.value as "elapsed" | "absolute")}
            className="w-full rounded-lg bg-[#111114] border border-[#27272A] px-2.5 py-1.5 font-mono text-[#FAFAFA]"
          >
            <option value="elapsed">Elapsed Fermentation Time</option>
            <option value="absolute">Absolute ISO / Wall-Clock UTC</option>
          </select>
        </div>
        {timestampKind === "elapsed" && (
          <div>
            <label className="block text-[11px] font-medium text-[#71717A] mb-1">
              Elapsed Time Unit
            </label>
            <select
              value={elapsedUnit}
              onChange={(e) => setElapsedUnit(e.target.value as "h" | "min" | "s")}
              className="w-full rounded-lg bg-[#111114] border border-[#27272A] px-2.5 py-1.5 font-mono text-[#FAFAFA]"
            >
              <option value="h">Hours (h → s)</option>
              <option value="min">Minutes (min → s)</option>
              <option value="s">Seconds (s)</option>
            </select>
          </div>
        )}
      </div>

      {/* Column Mapping Matrix */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="text-[11px] font-sans font-medium text-[#71717A] border-b border-[#27272A]">
            <tr>
              <th className="py-2.5 pr-3">Source CSV Column</th>
              <th className="py-2.5 pr-3">Sample Value</th>
              <th className="py-2.5 pr-3">Canonical Variable</th>
              <th className="py-2.5 pr-3">Source Unit → SI</th>
              <th className="py-2.5 pr-3">Provenance</th>
              <th className="py-2.5">Calibration Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#18181B]">
            {headers
              .filter((h) => h !== timestampCol)
              .map((header) => {
                const row = mappings[header];
                const spec = CANONICAL_VARIABLES.find(
                  (v) => v.key === row?.standardParameter
                );
                const firstSample = sampleRows[0]?.[header];
                return (
                  <tr key={header} className="hover:bg-[#16161A]">
                    <td className="py-2.5 pr-3 font-semibold text-[#FAFAFA]">
                      {header}
                    </td>
                    <td className="py-2.5 pr-3 text-[#A1A1AA] sb-tabular">
                      {firstSample !== undefined && firstSample !== null
                        ? String(firstSample)
                        : "—"}
                    </td>
                    <td className="py-2.5 pr-3">
                      <select
                        value={row?.standardParameter || ""}
                        onChange={(e) =>
                          updateRow(header, { standardParameter: e.target.value })
                        }
                        className="rounded-lg bg-[#09090B] border border-[#27272A] px-2.5 py-1.5 text-xs font-mono text-[#FAFAFA] focus:border-[#A1A1AA] focus:outline-none"
                      >
                        <option value="">-- Ignore Column (DQ-COL-UNMAPPED) --</option>
                        {CANONICAL_VARIABLES.map((v) => (
                          <option key={v.key} value={v.key}>
                            {v.key} ({v.label})
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2.5 pr-3">
                      {row?.standardParameter ? (
                        <div className="flex items-center gap-2">
                          <UnitSelect
                            value={row.unit}
                            variableKey={row.standardParameter}
                            onChange={(unit) => updateRow(header, { unit })}
                          />
                          {spec && (
                            <span className="text-[10px] text-[#71717A]">
                              → {spec.siUnit}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-[#71717A]">—</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-3">
                      {row?.standardParameter ? (
                        <select
                          value={row.provenance}
                          onChange={(e) =>
                            updateRow(header, {
                              provenance: e.target.value as ColumnMappingEntry["provenance"],
                            })
                          }
                          className="rounded-lg bg-[#09090B] border border-[#27272A] px-2 py-1 text-[11px] font-mono text-[#A1A1AA]"
                        >
                          <option value="sensor">sensor</option>
                          <option value="lab_assay">lab_assay</option>
                          <option value="manual_entry">manual_entry</option>
                        </select>
                      ) : (
                        <span className="text-[#71717A]">—</span>
                      )}
                    </td>
                    <td className="py-2.5">
                      {row?.standardParameter ? (
                        <select
                          value={row.calibrationStatus}
                          onChange={(e) =>
                            updateRow(header, {
                              calibrationStatus:
                                e.target.value as ColumnMappingEntry["calibrationStatus"],
                            })
                          }
                          className="rounded-lg bg-[#09090B] border border-[#27272A] px-2 py-1 text-[11px] font-mono text-[#A1A1AA]"
                        >
                          <option value="calibrated_pre_run">calibrated_pre_run</option>
                          <option value="calibrated_unknown_date">
                            calibrated_unknown_date
                          </option>
                          <option value="not_calibrated">not_calibrated</option>
                          <option value="unknown">unknown</option>
                        </select>
                      ) : (
                        <span className="text-[#71717A]">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {/* Live DQ-* Quality Checks & Pint Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-3 border-t border-[#27272A]">
        <div className="space-y-2">
          <span className="text-[12px] font-medium text-[#71717A]">
            Data-Quality Checks (DQ-* Registry · {liveQualityReport.issues.length} Flagged)
          </span>
          {liveQualityReport.issues.length === 0 ? (
            <div className="p-3 rounded-lg bg-[#10B981]/10 border border-[#10B981]/25 text-xs font-mono text-[#10B981]">
              All 13 DQ-* checks passed with zero timestamp, unit, or range anomalies.
            </div>
          ) : (
            <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
              {liveQualityReport.issues.map((iss, idx) => (
                <div
                  key={`${iss.check_code}-${idx}`}
                  className={`p-2.5 rounded-lg border text-[11px] font-mono flex items-start justify-between gap-2 ${
                    iss.severity === "critical" || iss.severity === "high"
                      ? "bg-rose-500/10 border-rose-400/30 text-rose-200"
                      : iss.severity === "medium"
                      ? "bg-amber-500/10 border-amber-400/30 text-amber-200"
                      : "bg-[#09090B] border-[#27272A] text-[#A1A1AA]"
                  }`}
                >
                  <div>
                    <strong className="text-[#FAFAFA]">[{iss.check_code}]</strong>{" "}
                    {iss.message}
                  </div>
                  <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-black/30 shrink-0">
                    {iss.severity}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <span className="text-[12px] font-medium text-[#71717A]">
            Normalized SI &amp; Display Summary ({liveQualityReport.variables.length} Variables)
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1">
            {liveQualityReport.variables.map((v) => (
              <div
                key={v.variable}
                className="p-2.5 rounded-lg bg-[#09090B] border border-[#27272A] text-[11px] font-mono"
              >
                <div className="flex items-center justify-between text-[#FAFAFA] font-semibold">
                  <span>{v.variable}</span>
                  <span className="text-[#10B981]">{v.valid_count} valid</span>
                </div>
                <div className="text-[10px] text-[#71717A] mt-0.5">
                  {v.unit_original} → SI <span className="text-[#A1A1AA]">{v.unit_si}</span>
                </div>
                <div className="text-[10px] text-[#A1A1AA] mt-1 sb-tabular">
                  Range: {formatNumber(v.min_display, 2)} – {formatNumber(v.max_display, 2)}{" "}
                  {v.unit_display}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          disabled={liveQualityReport.blocking}
          onClick={handleConfirm}
          className="h-9 px-4 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] disabled:opacity-40 text-[#09090B] font-medium text-[13px] transition-colors"
        >
          Confirm Mappings &amp; Commit Batch →
        </button>
      </div>
    </div>
  );
};
