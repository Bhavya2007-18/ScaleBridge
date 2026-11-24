/**
 * Reusable scientific UI badges and cards enforcing docs/15_UI_UX_SPECIFICATION.md:
 * - Dark control-center palette (deep navy, precision cyan, bioluminescent green)
 * - Never display bare numbers without units
 * - Explicitly distinguish Live vs Simulated vs Sample, and Measured vs Estimated vs Assumed vs Calculated
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
import type { DataOrigin } from "@/lib/mockBioprocess";

export function DataOriginBadge({ origin }: { origin: DataOrigin }) {
  const map: Record<DataOrigin, { label: string; cls: string; dot: string }> = {
    live: {
      label: "LIVE TELEMETRY",
      cls: "bg-emerald-500/10 text-emerald-300 border-emerald-400/30",
      dot: "bg-emerald-400",
    },
    simulated: {
      label: "SIMULATED TWIN",
      cls: "bg-cyan-500/10 text-cyan-300 border-cyan-400/30",
      dot: "bg-cyan-400",
    },
    sample: {
      label: "SAMPLE DATASET",
      cls: "bg-amber-500/10 text-amber-300 border-amber-400/30",
      dot: "bg-amber-400",
    },
  };
  const cfg = map[origin];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium uppercase tracking-wider border ${cfg.cls}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${origin === "live" ? "animate-pulse" : ""}`} />
      {cfg.label}
    </span>
  );
}

export function NatureBadge({ nature }: { nature: ValueNature | EvidenceLevel }) {
  const styles: Record<string, string> = {
    measured: "bg-emerald-500/10 text-emerald-300 border-emerald-400/30",
    estimated: "bg-amber-500/10 text-amber-300 border-amber-400/30",
    assumed: "bg-violet-500/10 text-violet-300 border-violet-400/30",
    calculated: "bg-cyan-500/10 text-cyan-300 border-cyan-400/30",
    mixed: "bg-sky-500/10 text-sky-300 border-sky-400/30",
    insufficient: "bg-slate-800/80 text-slate-300 border-slate-600/60",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase tracking-wider border ${
        styles[nature] || styles.insufficient
      }`}
    >
      {nature}
    </span>
  );
}

export function ProvenanceBadge({ provenance }: { provenance: Provenance | string }) {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-900/90 text-slate-300 border border-slate-700/70">
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
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-400/30">
        Insufficient Evidence
      </span>
    );
  }
  if (outcome === "not_configured") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
        Not Configured
      </span>
    );
  }
  if (outcome === "not_triggered") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase tracking-wider bg-emerald-500/10 text-emerald-300 border border-emerald-400/30">
        Checked — Nominal
      </span>
    );
  }
  const map: Record<Severity, string> = {
    critical: "bg-rose-500/15 text-rose-300 border-rose-400/40",
    high: "bg-orange-500/15 text-orange-300 border-orange-400/40",
    medium: "bg-amber-500/15 text-amber-300 border-amber-400/35",
    low: "bg-sky-500/15 text-sky-300 border-sky-400/30",
    info: "bg-slate-800 text-slate-300 border-slate-700",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider border ${map[severity]}`}
    >
      {severity}
    </span>
  );
}

export function CompatBadge({ outcome }: { outcome: CompatOutcome }) {
  if (outcome === "compatible") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider bg-emerald-500/15 text-emerald-300 border border-emerald-400/30">
        Compatible
      </span>
    );
  }
  if (outcome === "incompatible") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider bg-rose-500/15 text-rose-300 border border-rose-400/40">
        Incompatible
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-400/35">
      Cannot Evaluate
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
      className={`rounded-xl border p-4 transition-colors ${
        isInsuff
          ? "bg-amber-950/20 border-amber-500/35"
          : "bg-[#080D18]/90 border-slate-800 hover:border-cyan-500/30"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[11px] font-semibold text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/25">
              {calc.formula_id} v{calc.formula_version}
            </span>
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
              {calc.scale} {calc.criterion_id ? `· ${calc.criterion_id}` : "· baseline"}
            </span>
            {calc.review_status === "pending_review" && (
              <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 px-1.5 py-0.5 rounded border border-amber-400/25">
                Pending Advisor Review
              </span>
            )}
          </div>
          <h4 className="text-sm font-display font-semibold text-slate-100 mt-1.5">{calc.formula_name}</h4>
        </div>
        <NatureBadge nature={calc.evidence_level} />
      </div>

      <div className="mt-3 px-3 py-2 bg-[#03060C] text-slate-200 rounded-lg border border-slate-800/80 font-mono text-xs flex flex-wrap items-center justify-between gap-2">
        <span className="text-slate-400">Equation: {calc.equation}</span>
        {calc.output && calc.status === "computed" && (
          <span className="text-emerald-300 font-bold text-sm sb-tabular">
            = {formatQuantity(calc.output, 4)}
          </span>
        )}
      </div>

      {isInsuff ? (
        <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-400/30 text-xs text-amber-200">
          <p className="font-semibold">Insufficient Evidence — Calculation Halted</p>
          <p className="mt-0.5 text-amber-300/90">
            Missing required input(s):{" "}
            <span className="font-mono font-semibold">{calc.missing_inputs.join(", ")}</span>
          </p>
        </div>
      ) : (
        <div className="mt-3">
          <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5">
            Traceable Inputs & Provenance
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {Object.entries(calc.inputs).map(([k, q]) => (
              <div
                key={k}
                className="flex items-center justify-between text-xs bg-[#040812] px-2.5 py-1.5 rounded-lg border border-slate-800"
              >
                <span className="font-mono font-medium text-slate-200 sb-tabular">
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
        <div className="mt-2.5 text-[11px] text-slate-400">
          <span className="font-semibold text-slate-300">Assumptions: </span>
          {calc.assumptions.join(" · ")}
        </div>
      )}

      {calc.warnings.length > 0 && (
        <div className="mt-2 space-y-1">
          {calc.warnings.map((w, idx) => (
            <div
              key={idx}
              className="text-[11px] text-amber-200 bg-amber-500/10 border border-amber-500/25 px-2.5 py-1.5 rounded-lg"
            >
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
