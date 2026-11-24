"use client";

import React, { useEffect, useState } from "react";
import { DataOriginBadge } from "@/components/ScientificBadges";
import type { DataOrigin } from "@/lib/mockBioprocess";

interface KpiCardProps {
  label: string;
  value: number;
  decimals?: number;
  unit: string;
  delta: string;
  status?: "nominal" | "watch" | "critical";
  sparkline?: number[];
  origin: DataOrigin;
}

export function KpiCard({
  label,
  value,
  decimals = 1,
  unit,
  delta,
  status = "nominal",
  sparkline = [],
  origin,
}: KpiCardProps) {
  const [displayVal, setDisplayVal] = useState<number>(value);

  useEffect(() => {
    const startVal = displayVal;
    const diff = value - startVal;
    if (Math.abs(diff) < 0.0001) {
      setDisplayVal(value);
      return;
    }
    const duration = 450;
    const startTime = performance.now();
    let frame = 0;

    const tick = (now: number) => {
      const t = Math.min(1, (now - startTime) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayVal(startVal + diff * eased);
      if (t < 1) {
        frame = requestAnimationFrame(tick);
      }
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const statusColor =
    status === "critical"
      ? "bg-rose-400"
      : status === "watch"
      ? "bg-amber-400"
      : "bg-[#10B981]";

  const strokeColor =
    status === "critical"
      ? "#FB7185"
      : status === "watch"
      ? "#F59E0B"
      : "#10B981";

  let sparkPath = "";
  if (sparkline.length >= 2) {
    const min = Math.min(...sparkline);
    const max = Math.max(...sparkline);
    const span = Math.max(0.0001, max - min);
    sparkPath = sparkline
      .map((v, i) => {
        const x = (i / (sparkline.length - 1)) * 84;
        const y = 24 - ((v - min) / span) * 20 - 2;
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }

  return (
    <div className="sb-surface rounded-[12px] p-4 flex flex-col justify-between hover:bg-[#16161A] transition-colors">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${statusColor}`} />
          <span className="text-[12px] font-medium text-[#A1A1AA] truncate">
            {label}
          </span>
        </div>
        <DataOriginBadge origin={origin} />
      </div>

      <div className="mt-3 flex items-end justify-between gap-2">
        <div>
          <div className="text-[22px] font-semibold tracking-[-0.02em] text-[#FAFAFA] sb-tabular">
            {displayVal.toFixed(decimals)}{" "}
            <span className="text-[12px] font-mono font-normal text-[#71717A]">{unit}</span>
          </div>
          <div className="mt-1 text-[11px] text-[#71717A]">{delta}</div>
        </div>

        {sparkPath && (
          <svg viewBox="0 0 84 26" className="w-20 h-7 shrink-0 overflow-visible">
            <path d={sparkPath} fill="none" stroke={strokeColor} strokeWidth="1.6" />
          </svg>
        )}
      </div>
    </div>
  );
}
