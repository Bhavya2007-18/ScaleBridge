"use client";

import React, { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Cpu,
  Database,
  FlaskConical,
  Gauge,
  Layers,
  ShieldCheck,
} from "lucide-react";
import { LandingNavbar } from "@/components/landing/LandingNavbar";
import { TelemetryPreview } from "@/components/landing/TelemetryPreview";
import { ScientificLoader } from "@/components/dashboard/ScientificLoader";
import { DataOriginBadge } from "@/components/ScientificBadges";
import { computeScaleUpPreview } from "@/lib/mockBioprocess";

const BioreactorScene = dynamic(
  () => import("@/components/three/BioreactorScene").then((mod) => mod.BioreactorScene),
  {
    ssr: false,
    loading: () => <ScientificLoader label="Loading 3D Bioreactor Digital Twin..." />,
  }
);

export default function ScaleBridgeLandingPage() {
  const [rpm, setRpm] = useState<number>(175);
  const [aerationVvm, setAerationVvm] = useState<number>(0.65);
  const [scrollProgress, setScrollProgress] = useState<number>(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalH = document.documentElement.scrollHeight - window.innerHeight;
      if (totalH > 0) {
        setScrollProgress(window.scrollY / totalH);
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const liveMetrics = useMemo(
    () =>
      computeScaleUpPreview({
        sourceVolumeL: 2.0,
        sourceRpm: 420,
        sourceImpellerM: 0.055,
        targetVolumeL: 150.0,
        targetRpm: rpm,
        targetImpellerM: 0.24,
        aerationVvm,
      }),
    [rpm, aerationVvm]
  );

  return (
    <div className="min-h-screen sb-grid-bg text-slate-100 overflow-x-hidden">
      <LandingNavbar />

      {/* 1. HERO: IMMERSIVE 3D BIOREACTOR EXPERIENCE */}
      <section
        id="digital-twin"
        className="relative pt-24 pb-16 lg:pt-28 lg:pb-24 max-w-7xl mx-auto px-6 min-h-[92vh] flex items-center"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center w-full">
          {/* Left Copy Column */}
          <div className="lg:col-span-6 space-y-6 z-10">
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-700/80 text-[11px] font-mono uppercase tracking-widest text-cyan-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Intelligent Bioprocess Control Ecosystem
              </span>
              <DataOriginBadge origin="simulated" />
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold tracking-tight text-slate-50 leading-[1.06]">
              Scale biology with{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-sky-300 to-emerald-300">
                deterministic physics
              </span>{" "}
              and live intelligence.
            </h1>

            <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-xl">
              ScaleBridge transforms complex bioprocesses into intelligent, understandable, and optimizable systems—unifying fermentation telemetry, reactor geometry, hydrodynamic physics, and AI-guided scale-up readiness in one workspace.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-[#03060C] font-mono font-semibold text-xs uppercase tracking-wider transition-colors"
              >
                Open Control Center
                <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="#telemetry"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-slate-200 font-mono text-xs uppercase tracking-wider transition-colors"
              >
                Interact With 3D Twin
              </a>
            </div>

            {/* Scientific Telemetry Readouts */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-slate-800/80">
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 block">
                  Power Density (P/V)
                </span>
                <span className="text-xl font-mono font-bold text-slate-100 sb-tabular">
                  {liveMetrics.targetPvWm3.toFixed(1)}{" "}
                  <span className="text-xs font-normal text-cyan-400">W/m³</span>
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 block">
                  Mass Transfer (kLa)
                </span>
                <span className="text-xl font-mono font-bold text-emerald-300 sb-tabular">
                  {liveMetrics.targetKlaPerH.toFixed(1)}{" "}
                  <span className="text-xs font-normal text-slate-400">1/h</span>
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 block">
                  Impeller Tip Speed
                </span>
                <span className="text-xl font-mono font-bold text-slate-100 sb-tabular">
                  {liveMetrics.targetTipSpeedMs.toFixed(2)}{" "}
                  <span className="text-xs font-normal text-cyan-400">m/s</span>
                </span>
              </div>
            </div>
          </div>

          {/* Right 3D Bioreactor Centerpiece with Floating HUD Telemetry */}
          <div className="lg:col-span-6 relative h-[480px] sm:h-[560px] rounded-3xl sb-surface overflow-hidden">
            <BioreactorScene
              rpm={rpm}
              aerationVvm={aerationVvm}
              scrollProgress={scrollProgress}
              interactive
            />

            {/* Floating Scientific Callout: Top Left */}
            <div className="absolute top-5 left-5 px-3.5 py-2.5 rounded-xl sb-glass pointer-events-none">
              <div className="flex items-center gap-2 text-[10px] font-mono uppercase text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Broth Vitality · Simulated
              </div>
              <div className="mt-1 flex items-baseline gap-3 font-mono text-xs sb-tabular">
                <span className="text-slate-100 font-semibold">36.8 °C</span>
                <span className="text-cyan-300">pH 7.05</span>
                <span className="text-emerald-300">dO₂ 40.5%</span>
              </div>
            </div>

            {/* Floating Scientific Callout: Top Right */}
            <div className="absolute top-5 right-5 px-3 py-1.5 rounded-full sb-glass text-[10px] font-mono text-slate-300 pointer-events-none">
              DRAG TO ORBIT · 150 L SUB TWIN
            </div>

            {/* Floating Scientific Callout: Bottom */}
            <div className="absolute bottom-5 inset-x-5 flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 rounded-xl sb-glass text-[11px] font-mono pointer-events-none">
              <span className="text-slate-300">
                Impeller: <strong className="text-cyan-300">{rpm} RPM</strong> · Gas Sparge:{" "}
                <strong className="text-emerald-300">{aerationVvm.toFixed(2)} vvm</strong>
              </span>
              <span className="text-slate-400 uppercase">
                Regime: <strong className="text-slate-100">{liveMetrics.regime}</strong>
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. THE SCALE-UP CHALLENGE & PLATFORM SOLUTION */}
      <section id="challenge" className="py-20 border-t border-slate-800/70 bg-[#03060C]/60">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div className="max-w-2xl">
            <span className="text-xs font-mono uppercase tracking-widest text-cyan-400">
              01 // Why Bioprocess Transfers Fail
            </span>
            <h2 className="mt-2 text-3xl sm:text-4xl font-display font-bold text-slate-100">
              Lab success breaks when vessel geometry changes.
            </h2>
            <p className="mt-3 text-sm text-slate-400 leading-relaxed">
              Moving a fermentation process from a 2 L benchtop reactor to 200 L pilot or 2,000 L GMP tanks cannot preserve power density, tip speed, oxygen transfer, and mixing time simultaneously. ScaleBridge makes every trade-off explicit before a single liter is inoculated.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Gauge,
                tag: "Hydrodynamics & Shear",
                title: "Coupled P/V vs. Tip Speed",
                body: "Calculates exact shaft power density, Rushton/hydrofoil tip velocities, and turbulent Reynolds regimes across non-similar vessel geometries using Pint-verified dimensional units.",
                accent: "text-cyan-400",
              },
              {
                icon: Activity,
                tag: "Mass & Heat Transfer",
                title: "OTR Bottlenecks & Insufficient Evidence",
                body: "Evaluates Van't Riet kLa predictions against metabolic oxygen demand while explicitly halting and flagging missing broth rheology or cooling jacket measurements.",
                accent: "text-emerald-400",
              },
              {
                icon: ShieldCheck,
                tag: "Audit-Ready Transfer",
                title: "Explainable Risk & Validation Plans",
                body: "Translates hardware shortfalls and kinetic anomalies into prioritized pre-transfer experiments, reviewer sign-offs, and provenance-hashed transfer dossiers.",
                accent: "text-sky-400",
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="sb-surface rounded-2xl p-6 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center">
                      <Icon className={`w-5 h-5 ${item.accent}`} />
                    </div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      {item.tag}
                    </span>
                  </div>
                  <h3 className="text-lg font-display font-semibold text-slate-100">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-xs text-slate-400 leading-relaxed">{item.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 3. INTERACTIVE DIGITAL TWIN TELEMETRY & DATA VISUALIZATION */}
      <section id="telemetry" className="py-20 border-t border-slate-800/70">
        <div className="max-w-7xl mx-auto px-6 space-y-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="max-w-2xl">
              <span className="text-xs font-mono uppercase tracking-widest text-emerald-400">
                02 // Real-Time Telemetry &amp; Process Curves
              </span>
              <h2 className="mt-2 text-3xl sm:text-4xl font-display font-bold text-slate-100">
                Observe biology, hydrodynamics, and nutrient kinetics together.
              </h2>
            </div>
            <Link
              href="/dashboard"
              className="text-xs font-mono uppercase tracking-wider text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1.5"
            >
              Launch Full Analytics Workspace <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <TelemetryPreview
            rpm={rpm}
            aerationVvm={aerationVvm}
            onRpmChange={setRpm}
            onAerationChange={setAerationVvm}
          />
        </div>
      </section>

      {/* 4. UNIFIED ECOSYSTEM ARCHITECTURE */}
      <section id="ecosystem" className="py-20 border-t border-slate-800/70 bg-[#03060C]/70">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div className="max-w-2xl">
            <span className="text-xs font-mono uppercase tracking-widest text-cyan-400">
              03 // One Intelligent Ecosystem
            </span>
            <h2 className="mt-2 text-3xl sm:text-4xl font-display font-bold text-slate-100">
              From raw bioreactor logs to verified manufacturing readiness.
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              {
                step: "01",
                icon: FlaskConical,
                title: "Process Passport",
                desc: "Versioned biological context, medium properties, CPPs, and CQAs with explicit Measured vs. Assumed tags.",
              },
              {
                step: "02",
                icon: Database,
                title: "Data Ingestion",
                desc: "Vendor-agnostic CSV ingestion normalizing Sartorius, Eppendorf, and Cytiva streams into Pint SI units.",
              },
              {
                step: "03",
                icon: Layers,
                title: "Digital Twin Engine",
                desc: "Multi-criteria scale-up modeling across constant P/V, tip speed, VVM, and vessel hardware envelopes.",
              },
              {
                step: "04",
                icon: Cpu,
                title: "AI & Validation Plan",
                desc: "Prioritized commissioning checks, AI optimization insights, reviewer sign-offs, and PDF transfer reports.",
              },
            ].map((node) => {
              const Icon = node.icon;
              return (
                <div
                  key={node.step}
                  className="sb-surface rounded-2xl p-5 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="font-mono text-xs text-cyan-400 font-semibold">
                        STAGE {node.step}
                      </span>
                      <Icon className="w-4 h-4 text-slate-400" />
                    </div>
                    <h3 className="text-base font-display font-semibold text-slate-100">
                      {node.title}
                    </h3>
                    <p className="mt-2 text-xs text-slate-400 leading-relaxed">{node.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Closing CTA */}
          <div className="sb-surface rounded-3xl p-8 sm:p-12 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-widest text-emerald-400">
                Biotechnology Control Center
              </span>
              <h3 className="mt-2 text-2xl sm:text-3xl font-display font-bold text-slate-100">
                Enter the ScaleBridge Engineering Workspace
              </h3>
              <p className="mt-2 text-xs sm:text-sm text-slate-400 max-w-xl">
                Explore live or simulated CHO fed-batch telemetry, compare 2 L to 2,000 L bioreactors, run deterministic scale-up assessments, and inspect AI optimization insights.
              </p>
            </div>
            <Link
              href="/dashboard"
              className="shrink-0 inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl bg-emerald-400 hover:bg-emerald-300 text-[#03060C] font-mono font-bold text-xs uppercase tracking-wider transition-colors"
            >
              Launch Control Center
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-800/80 py-8 px-6 text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span>SCALEBRIDGE BIO // DETERMINISTIC BIOPROCESS INTELLIGENCE</span>
          <span>LANDING TELEMETRY CLEARLY LABELED AS SIMULATED / SAMPLE DATA</span>
        </div>
      </footer>
    </div>
  );
}
