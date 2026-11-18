/**
 * Reusable scientific UI badges and cards enforcing docs/15_UI_UX_SPECIFICATION.md:
 * - Never display bare numbers without units
 * - Explicitly distinguish Measured vs Estimated vs Assumed vs Calculated
 * - Render "Insufficient evidence" as a first-class structured card
 */

import React from "react";
import {
  CalculationResult,
  CompatOutcome,
  EvidenceLevel,
  Provenance,
  Quantity,
  RuleOutcome,
  Severity,
  ValueNature,
} from "@/lib/api";

export function NatureBadge({ nature }: { nature: ValueNature | EvidenceLevel }) {
  const styles: Record<string, string> = {
    measured: "bg-emerald-50 text-emerald-800 border-emerald-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    assumed: "bg-purple-50 text-purple-800 border-purple-200",
    calculated: "bg-teal-50 text-teal-800 border-teal-200",
    mixed: "bg-blue-50 text-blue-800 border-blue-200",
    insufficient: "bg-stone-100 text-stone-700 border-stone-300",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
        styles[nature] || styles.insufficient
      }`}
    >
      {nature.toUpperCase()}
    </span>
  );
}

export function ProvenanceBadge({ provenance }: { provenance: Provenance | string }) {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-700 border border-slate-200">
      {provenance.replace(/_/g, " ")}
    </span>
  );
}

export function SeverityBadge({
  severity,
  outcome,
}: {
  severity: Severity;
  outcome?: RuleOutcome;
}) {
  if (outcome === "insufficient_evidence") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300">
        INSUFFICIENT EVIDENCE
      </span>
    );
  }
  if (outcome === "not_configured") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-300">
        NOT CONFIGURED
      </span>
    );
  }
  if (outcome === "not_triggered") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        CHECKED — OK
      </span>
    );
  }
  const map: Record<Severity, string> = {
    critical: "bg-red-100 text-red-900 border-red-300",
    high: "bg-orange-100 text-orange-900 border-orange-300",
    medium: "bg-amber-100 text-amber-900 border-amber-300",
    low: "bg-blue-50 text-blue-800 border-blue-200",
    info: "bg-slate-100 text-slate-700 border-slate-200",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${map[severity]}`}
    >
      {severity.toUpperCase()}
    </span>
  );
}

export function CompatBadge({ outcome }: { outcome: CompatOutcome }) {
  if (outcome === "compatible") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
        COMPATIBLE
      </span>
    );
  }
  if (outcome === "incompatible") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 border border-red-300">
        INCOMPATIBLE
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300">
      CANNOT EVALUATE
    </span>
  );
}

export function formatQuantity(q: Quantity | null | undefined, digits = 3): string {
  if (!q || q.value === null || q.value === undefined) {
    return "Insufficient evidence";
  }
  const val = q.display_value !== null && q.display_value !== undefined ? q.display_value : q.value;
  const unit = q.display_unit || q.unit;
  const formatted =
    Math.abs(val) >= 1000 || (Math.abs(val) > 0 && Math.abs(val) < 0.01)
      ? val.toPrecision(digits)
      : Number(val.toFixed(digits)).toString();
  return unit === "dimensionless" ? formatted : `${formatted} ${unit}`;
}

export function CalculationTraceCard({ calc }: { calc: CalculationResult }) {
  const isInsuff = calc.status === "insufficient_evidence";
  return (
    <div
      className={`rounded-lg border p-4 shadow-sm ${
        isInsuff ? "bg-amber-50/40 border-amber-300" : "bg-white border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
              {calc.formula_id} v{calc.formula_version}
            </span>
            <span className="text-xs uppercase font-semibold text-slate-500">
              {calc.scale} {calc.criterion_id ? `· ${calc.criterion_id}` : "· baseline"}
            </span>
            {calc.review_status === "pending_review" && (
              <span className="text-[11px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded border border-amber-300">
                Pending Advisor Review
              </span>
            )}
          </div>
          <h4 className="text-sm font-semibold text-slate-900 mt-1">{calc.formula_name}</h4>
        </div>
        <NatureBadge nature={calc.evidence_level} />
      </div>

      <div className="mt-2 px-3 py-1.5 bg-slate-900 text-slate-100 rounded font-mono text-xs flex items-center justify-between">
        <span>Equation: {calc.equation}</span>
        {calc.output && calc.status === "computed" && (
          <span className="text-teal-300 font-bold text-sm">
            = {formatQuantity(calc.output, 4)}
          </span>
        )}
      </div>

      {isInsuff ? (
        <div className="mt-3 p-2.5 rounded bg-amber-100/70 border border-amber-300 text-xs text-amber-950">
          <p className="font-semibold">Insufficient Evidence — Calculation Blocked</p>
          <p className="mt-0.5">
            Missing required input(s):{" "}
            <span className="font-mono font-semibold">{calc.missing_inputs.join(", ")}</span>
          </p>
        </div>
      ) : (
        <div className="mt-3">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Traceable Inputs & Provenance
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {Object.entries(calc.inputs).map(([k, q]) => (
              <div
                key={k}
                className="flex items-center justify-between text-xs bg-slate-50 px-2.5 py-1 rounded border border-slate-200"
              >
                <span className="font-mono font-semibold text-slate-700">
                  {k} = {formatQuantity(q, 4)}
                </span>
                <div className="flex items-center gap-1">
                  <ProvenanceBadge provenance={q.provenance} />
                  <NatureBadge nature={q.value_nature} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {calc.assumptions.length > 0 && (
        <div className="mt-2.5 text-[11px] text-slate-600">
          <span className="font-semibold text-slate-700">Assumptions: </span>
          {calc.assumptions.join(" · ")}
        </div>
      )}

      {calc.warnings.length > 0 && (
        <div className="mt-2 space-y-1">
          {calc.warnings.map((w, idx) => (
            <div
              key={idx}
              className="text-[11px] text-amber-900 bg-amber-50 border border-amber-200 px-2 py-1 rounded"
            >
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
