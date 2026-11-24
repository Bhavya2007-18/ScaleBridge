"use client";

import React from "react";

interface ScientificLoaderProps {
  label?: string;
  compact?: boolean;
}

export function ScientificLoader({
  label = "Initializing Bioreactor Digital Twin...",
  compact = false,
}: ScientificLoaderProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center ${
        compact ? "py-10" : "min-h-[320px]"
      } text-center select-none`}
    >
      <div className="relative w-16 h-16 flex items-center justify-center">
        {/* Outer precision telemetry ring */}
        <div className="absolute inset-0 rounded-full border border-cyan-400/30 border-t-cyan-400 animate-spin" />
        {/* Inner bioluminescent impeller ring */}
        <div
          className="absolute inset-2.5 rounded-full border border-emerald-400/25 border-b-emerald-400 animate-spin"
          style={{ animationDirection: "reverse", animationDuration: "2.4s" }}
        />
        {/* Core cellular pulse */}
        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.8)] animate-pulse" />
      </div>
      <p className="mt-4 text-xs font-mono tracking-wider uppercase text-slate-400">
        {label}
      </p>
    </div>
  );
}
