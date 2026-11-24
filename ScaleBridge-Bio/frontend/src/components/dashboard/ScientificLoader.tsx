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
      <div className="relative w-14 h-14 flex items-center justify-center">
        <div className="absolute inset-0 rounded-full border border-[#27272A] border-t-[#FAFAFA] animate-spin" />
        <div
          className="absolute inset-2.5 rounded-full border border-[#27272A] border-b-[#10B981] animate-spin"
          style={{ animationDirection: "reverse", animationDuration: "2.4s" }}
        />
        <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
      </div>
      <p className="mt-4 text-[12px] font-medium text-[#71717A]">
        {label}
      </p>
    </div>
  );
}
