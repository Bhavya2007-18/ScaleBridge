"use client";

import React from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function LandingNavbar() {
  return (
    <header className="fixed top-0 inset-x-0 z-50 sb-glass border-b border-slate-800/70">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-slate-900 border border-cyan-400/35 flex items-center justify-center">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.75)] group-hover:scale-110 transition-transform" />
          </div>
          <div className="leading-tight">
            <span className="font-display font-bold tracking-tight text-base text-slate-100 block">
              ScaleBridge<span className="text-cyan-400 font-normal">.bio</span>
            </span>
            <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-400 block">
              Bioprocess Digital Twin
            </span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8 text-xs font-mono uppercase tracking-wider text-slate-400">
          <a href="#digital-twin" className="hover:text-cyan-300 transition-colors">
            Digital Twin
          </a>
          <a href="#challenge" className="hover:text-cyan-300 transition-colors">
            Scale Physics
          </a>
          <a href="#telemetry" className="hover:text-cyan-300 transition-colors">
            Telemetry
          </a>
          <a href="#ecosystem" className="hover:text-cyan-300 transition-colors">
            Ecosystem
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/25 text-[10px] font-mono text-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            SYSTEM ONLINE
          </div>
          <Link
            href="/login"
            className="hidden sm:inline-flex items-center px-3 py-2 rounded-lg text-slate-300 hover:text-white font-mono text-xs uppercase tracking-wider transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-400 hover:bg-cyan-300 text-[#03060C] font-mono font-semibold text-xs uppercase tracking-wider transition-colors"
          >
            Control Center
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </header>
  );
}
