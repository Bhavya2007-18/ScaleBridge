"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function LandingNavbar() {
  return (
    <header className="fixed top-0 inset-x-0 z-50 h-16 bg-[#09090B]/85 backdrop-blur-md border-b border-[#18181B]">
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-md bg-[#111114] border border-[#27272A] flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]">
            <span className="w-2 h-2 rounded-full bg-[#10B981]" />
          </div>
          <span className="font-semibold tracking-[-0.02em] text-[15px] text-[#FAFAFA]">
            ScaleBridge<span className="text-[#71717A] font-normal">.bio</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-7 text-[13px] font-medium text-[#A1A1AA]">
          <a href="#digital-twin" className="hover:text-[#FAFAFA] transition-colors">
            Digital Twin
          </a>
          <a href="#challenge" className="hover:text-[#FAFAFA] transition-colors">
            Scale Physics
          </a>
          <a href="#telemetry" className="hover:text-[#FAFAFA] transition-colors">
            Telemetry
          </a>
          <a href="#ecosystem" className="hover:text-[#FAFAFA] transition-colors">
            Ecosystem
          </a>
        </nav>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 text-[12px] font-medium text-[#A1A1AA]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
            <span>Operational</span>
          </div>
          <Link
            href="/login"
            className="hidden sm:inline-flex items-center text-[13px] font-medium text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors"
          >
            Sign in
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
          >
            <span>Control Center</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </header>
  );
}
