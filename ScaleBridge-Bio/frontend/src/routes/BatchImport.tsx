"use client";

import React, { useState } from "react";
import { ColumnMapper, ColumnMappingEntry } from "../components/ColumnMapper";
import { SYNTHETIC_GOLDEN_CSV } from "../lib/format";
import type { QualityReport } from "../lib/api";

function parseCsvText(csvText: string): {
  headers: string[];
  rows: Array<Record<string, string | number | null>>;
} {
  const lines = csvText
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
  const rows = lines.slice(1).map((line) => {
    const cells = line.split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
    const rec: Record<string, string | number | null> = {};
    headers.forEach((h, i) => {
      const v = cells[i] ?? "";
      const num = Number(v);
      rec[h] = v === "" ? null : !Number.isNaN(num) ? num : v;
    });
    return rec;
  });
  return { headers, rows };
}

export const BatchImport: React.FC = () => {
  const [runCode, setRunCode] = useState("LAB-2L-RUN-03");
  const [workingVolL, setWorkingVolL] = useState(2.0);
  const [sourceDesc, setSourceDesc] = useState("Sartorius Biostat B-DCU 2L CSV export");
  const [isSynthetic, setIsSynthetic] = useState(true);
  const [headers, setHeaders] = useState<string[]>(() => parseCsvText(SYNTHETIC_GOLDEN_CSV).headers);
  const [sampleRows, setSampleRows] = useState<Array<Record<string, string | number | null>>>(
    () => parseCsvText(SYNTHETIC_GOLDEN_CSV).rows
  );
  const [committedReport, setCommittedReport] = useState<QualityReport | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = (event.target?.result as string) || "";
      const parsed = parseCsvText(text);
      setHeaders(parsed.headers);
      setSampleRows(parsed.rows);
      setCommittedReport(null);
      setStatusMessage(`Parsed ${parsed.rows.length} rows and ${parsed.headers.length} columns from ${file.name}.`);
    };
    reader.readAsText(file);
  };

  const handleLoadSyntheticSample = () => {
    const parsed = parseCsvText(SYNTHETIC_GOLDEN_CSV);
    setHeaders(parsed.headers);
    setSampleRows(parsed.rows);
    setIsSynthetic(true);
    setCommittedReport(null);
    setStatusMessage("Loaded synthetic golden 120 h fed-batch reference dataset.");
  };

  const handleSaveMappings = (
    mappings: ColumnMappingEntry[],
    tsCfg: { column: string; kind: "elapsed" | "absolute"; elapsedUnit: "h" | "min" | "s" },
    report: QualityReport
  ) => {
    setCommittedReport(report);
    setStatusMessage(
      `Imported batch '${runCode}' (${report.rows_imported} rows, ${mappings.length} Pint-normalized variables, time axis: ${tsCfg.column} [${tsCfg.kind}]).`
    );
  };

  return (
    <div className="space-y-6">
      <div className="sb-surface rounded-2xl p-6 space-y-4 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400">
              Domain B // Experimental Batch Ingestion Pipeline
            </span>
            <h1 className="text-2xl font-display font-bold text-slate-100 mt-0.5">
              Ingest &amp; Normalize Bioreactor Telemetry
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Upload raw CSV exports (Sartorius, Eppendorf, Cytiva, Applikon), map headers to the canonical bioprocess vocabulary, and run automated DQ-* checks.
            </p>
          </div>
          <button
            type="button"
            onClick={handleLoadSyntheticSample}
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-cyan-400/30 text-cyan-300 font-mono text-xs uppercase tracking-wider shrink-0"
          >
            Load Golden 120h Reference CSV
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 text-xs">
          <div>
            <label className="block font-mono text-slate-400 mb-1">Batch Run Code</label>
            <input
              value={runCode}
              onChange={(e) => setRunCode(e.target.value)}
              className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 font-mono text-slate-100"
            />
          </div>
          <div>
            <label className="block font-mono text-slate-400 mb-1">Working Volume (L)</label>
            <input
              type="number"
              step="0.1"
              value={workingVolL}
              onChange={(e) => setWorkingVolL(Number(e.target.value))}
              className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 font-mono text-slate-100"
            />
          </div>
          <div>
            <label className="block font-mono text-slate-400 mb-1">Source Instrument</label>
            <input
              value={sourceDesc}
              onChange={(e) => setSourceDesc(e.target.value)}
              className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 font-mono text-slate-100"
            />
          </div>
          <div>
            <label className="block font-mono text-slate-400 mb-1">Upload CSV File</label>
            <input
              type="file"
              accept=".csv,.txt"
              onChange={handleFileUpload}
              className="w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-slate-800 file:text-cyan-300 file:font-mono"
            />
          </div>
        </div>

        <label className="inline-flex items-center gap-2 text-xs font-mono text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={isSynthetic}
            onChange={(e) => setIsSynthetic(e.target.checked)}
            className="accent-cyan-400"
          />
          <span>Tag dataset as Synthetic / Demonstration Data (triggers R-DAT-005 audit watermark)</span>
        </label>

        {statusMessage && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-400/30 text-xs font-mono text-emerald-300">
            {statusMessage}
          </div>
        )}
      </div>

      {headers.length > 0 && (
        <ColumnMapper
          headers={headers}
          sampleRows={sampleRows}
          onSaveMappings={handleSaveMappings}
        />
      )}

      {committedReport && (
        <div className="sb-surface rounded-2xl p-5 border border-emerald-400/30 space-y-2 text-xs font-mono">
          <div className="text-emerald-300 font-semibold">
            ✓ Batch Transaction Committed — {committedReport.rows_imported} time-series points normalized via Pint
          </div>
          <div className="text-slate-400">
            Variables stored with dual (original + SI) representation:{" "}
            {committedReport.variables.map((v) => `${v.variable} [${v.unit_original} → ${v.unit_si}]`).join(" · ")}
          </div>
        </div>
      )}
    </div>
  );
};
