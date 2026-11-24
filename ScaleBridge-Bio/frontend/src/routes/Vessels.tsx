"use client";

import React, { useState } from "react";
import { useVessels } from "../api/hooks/useData";
import { VesselCompareTable } from "../components/VesselCompareTable";
import type { Vessel } from "../api/types";

export const Vessels: React.FC = () => {
  const { vessels, loading, error } = useVessels();
  const [sourceIdx, setSourceIdx] = useState(0);
  const [targetIdx, setTargetIdx] = useState(1);
  const [customVessels, setCustomVessels] = useState<Vessel[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);

  // New vessel form state
  const [newName, setNewName] = useState("BioFlo 500L Pilot Stainless");
  const [newScale, setNewScale] = useState<"lab" | "pilot" | "production">("pilot");
  const [newVolMin, setNewVolMin] = useState(150);
  const [newVolMax, setNewVolMax] = useState(500);
  const [newMaxRpm, setNewMaxRpm] = useState(320);
  const [newMaxPower, setNewMaxPower] = useState(4500);
  const [newMaxVvm, setNewMaxVvm] = useState(1.1);
  const [newImpeller, setNewImpeller] = useState("Rushton, Hydrofoil");

  const allVessels = [...vessels, ...customVessels];
  const srcVessel = allVessels[sourceIdx] || allVessels[0];
  const tgtVessel = allVessels[targetIdx] || allVessels[1] || allVessels[0];

  const handleAddVessel = (e: React.FormEvent) => {
    e.preventDefault();
    const created: Vessel = {
      id: `vess_custom_${Date.now()}`,
      name: newName,
      facility: "Pilot Engineering Bay",
      scale_category: newScale,
      working_volume_min_l: newVolMin,
      working_volume_max_l: newVolMax,
      total_volume_l: Number((newVolMax * 1.25).toFixed(1)),
      aspect_ratio: 2.4,
      impeller_count: 2,
      impeller_types: newImpeller.split(",").map((s) => s.trim()),
      baffle_count: 4,
      sparger_type: "Ring Sparger",
      max_rpm: newMaxRpm,
      max_power_w: newMaxPower,
      max_gassing_vvm: newMaxVvm,
    };
    setCustomVessels((prev) => [...prev, created]);
    setShowAddForm(false);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono uppercase tracking-widest text-[#2fe578] mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2fe578]" />
            Hardware Custody Registry (docs/13)
          </div>
          <h1 className="text-3xl font-display font-bold text-white">
            Bioreactor Equipment Fleet &amp; Geometry Matrix
          </h1>
          <p className="text-xs text-[#8e9e94] mt-1 font-light">
            Calibrated physical geometries, motor utility ceilings, and side-by-side D/T &amp; H_L/T similarity checks across lab, pilot, and production vessels.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAddForm((v) => !v)}
          className="px-4 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-[#03060C] font-mono font-semibold text-xs uppercase tracking-wider shrink-0"
        >
          {showAddForm ? "Cancel" : "+ Register New Vessel Profile"}
        </button>
      </div>

      {showAddForm && (
        <form
          onSubmit={handleAddVessel}
          className="sb-surface rounded-2xl p-6 border border-cyan-400/30 space-y-4 text-xs"
        >
          <h3 className="text-base font-display font-bold text-slate-100">
            Register New Bioreactor Profile
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 font-mono">
            <div>
              <label className="block text-slate-400 mb-1">Vessel Name</label>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Scale Class</label>
              <select
                value={newScale}
                onChange={(e) => setNewScale(e.target.value as "lab" | "pilot" | "production")}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              >
                <option value="lab">lab</option>
                <option value="pilot">pilot</option>
                <option value="production">production</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Min Working Vol (L)</label>
              <input
                type="number"
                value={newVolMin}
                onChange={(e) => setNewVolMin(Number(e.target.value))}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Max Working Vol (L)</label>
              <input
                type="number"
                value={newVolMax}
                onChange={(e) => setNewVolMax(Number(e.target.value))}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Max Agitation (RPM)</label>
              <input
                type="number"
                value={newMaxRpm}
                onChange={(e) => setNewMaxRpm(Number(e.target.value))}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Motor Power Limit (W)</label>
              <input
                type="number"
                value={newMaxPower}
                onChange={(e) => setNewMaxPower(Number(e.target.value))}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Max Gassing (VVM)</label>
              <input
                type="number"
                step="0.1"
                value={newMaxVvm}
                onChange={(e) => setNewMaxVvm(Number(e.target.value))}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Impeller Types</label>
              <input
                value={newImpeller}
                onChange={(e) => setNewImpeller(e.target.value)}
                className="w-full rounded-xl bg-[#040812] border border-slate-800 px-3 py-2 text-slate-100"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-[#03060C] font-mono font-semibold text-xs uppercase tracking-wider"
          >
            Save Vessel to Fleet Registry
          </button>
        </form>
      )}

      {loading && (
        <div className="text-xs font-mono text-[#708076] py-12 text-center">
          Reading vessel calibration blocks...
        </div>
      )}
      {error && (
        <div className="text-xs font-mono text-rose-400 py-6 text-center">
          [Sync Error]: {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {allVessels.map((v) => (
          <div key={v.id} className="p-6 rounded-3xl euronium-glass-card space-y-4">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="px-2.5 py-0.5 rounded-full bg-[#2fe578]/10 border border-[#2fe578]/30 text-[#2fe578] text-[10px] uppercase font-semibold">
                {v.scale_category} NODE
              </span>
              <span className="text-[10px] text-[#708076]">{v.facility || "Facility #01"}</span>
            </div>

            <div>
              <h3 className="font-display font-bold text-lg text-white">{v.name}</h3>
              <p className="text-xs font-mono text-[#7cf6b1] mt-0.5">
                Volumetric Span: {v.working_volume_min_l}L – {v.working_volume_max_l}L
              </p>
            </div>

            <div className="space-y-2 pt-3 border-t border-white/5 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-white/[0.03]">
                <span className="text-[#8e9e94]">Agitation Speed Ceiling</span>
                <span className="text-white">{v.max_rpm ?? "—"} RPM</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.03]">
                <span className="text-[#8e9e94]">Motor Utility Power</span>
                <span className="text-white">{v.max_power_w ?? "—"} Watts</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.03]">
                <span className="text-[#8e9e94]">Aeration Envelope</span>
                <span className="text-white">{v.max_gassing_vvm ?? "—"} VVM</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#8e9e94]">Impeller Architecture</span>
                <span className="text-[#d0ded5] text-right truncate max-w-[160px]">
                  {v.impeller_types.join(", ")}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {srcVessel && tgtVessel && (
        <div className="space-y-3 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-display font-bold text-white">
              Side-by-Side Vessel Comparison
            </h2>
            <div className="flex items-center gap-3 text-xs font-mono">
              <select
                value={sourceIdx}
                onChange={(e) => setSourceIdx(Number(e.target.value))}
                className="rounded-xl bg-[#040812] border border-slate-800 px-3 py-1.5 text-slate-200"
              >
                {allVessels.map((v, idx) => (
                  <option key={v.id} value={idx}>
                    Source: {v.name}
                  </option>
                ))}
              </select>
              <span className="text-slate-500">→</span>
              <select
                value={targetIdx}
                onChange={(e) => setTargetIdx(Number(e.target.value))}
                className="rounded-xl bg-[#040812] border border-slate-800 px-3 py-1.5 text-cyan-300"
              >
                {allVessels.map((v, idx) => (
                  <option key={v.id} value={idx}>
                    Target: {v.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <VesselCompareTable sourceVessel={srcVessel} targetVessel={tgtVessel} />
        </div>
      )}
    </div>
  );
};
