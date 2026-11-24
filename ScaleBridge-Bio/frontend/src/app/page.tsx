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
    <div className="min-h-screen bg-[#09090B] text-[#FAFAFA] overflow-x-hidden">
      <LandingNavbar />

      {/* 1. HERO: BIOREACTOR DIGITAL TWIN */}
      <section
        id="digital-twin"
        className="relative pt-24 pb-20 lg:pt-28 lg:pb-24 max-w-7xl mx-auto px-6 min-h-[90vh] flex items-center"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center w-full">
          {/* Left Copy Column */}
          <div className="lg:col-span-6 space-y-6 z-10">
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-2 text-[12px] font-semibold text-[#10B981]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
                Bioprocess Scale-Up Intelligence
              </span>
              <DataOriginBadge origin="simulated" />
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[52px] font-semibold tracking-[-0.03em] text-[#FAFAFA] leading-[1.08]">
              Scale biology with deterministic physics and live intelligence.
            </h1>

            <p className="text-[15px] text-[#A1A1AA] leading-[1.6] max-w-xl">
              ScaleBridge transforms fermentation process transfers into auditable engineering decisions—unifying batch telemetry, vessel geometry, hydrodynamic physics, and risk readiness in one workspace.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 h-10 px-5 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
              >
                <span>Open Control Center</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <a
                href="#telemetry"
                className="inline-flex items-center gap-2 h-10 px-5 rounded-lg bg-[#111114] hover:bg-[#16161A] border border-[#27272A] text-[#FAFAFA] font-medium text-[13px] transition-colors"
              >
                Interact with Digital Twin
              </a>
            </div>

            {/* Scientific Telemetry Readouts */}
            <div className="grid grid-cols-3 gap-6 pt-6 border-t border-[#27272A]">
              <div>
                <span className="text-[12px] font-medium text-[#71717A] block">
                  Power Density (P/V)
                </span>
                <span className="text-[20px] font-semibold tracking-[-0.02em] text-[#FAFAFA] sb-tabular mt-1 inline-block">
                  {liveMetrics.targetPvWm3.toFixed(1)}{" "}
                  <span className="text-[12px] font-mono font-normal text-[#71717A]">W/m³</span>
                </span>
              </div>
              <div>
                <span className="text-[12px] font-medium text-[#71717A] block">
                  Mass Transfer (kLa)
                </span>
                <span className="text-[20px] font-semibold tracking-[-0.02em] text-[#FAFAFA] sb-tabular mt-1 inline-block">
                  {liveMetrics.targetKlaPerH.toFixed(1)}{" "}
                  <span className="text-[12px] font-mono font-normal text-[#71717A]">1/h</span>
                </span>
              </div>
              <div>
                <span className="text-[12px] font-medium text-[#71717A] block">
                  Impeller Tip Speed
                </span>
                <span className="text-[20px] font-semibold tracking-[-0.02em] text-[#FAFAFA] sb-tabular mt-1 inline-block">
                  {liveMetrics.targetTipSpeedMs.toFixed(2)}{" "}
                  <span className="text-[12px] font-mono font-normal text-[#71717A]">m/s</span>
                </span>
              </div>
            </div>
          </div>

          {/* Right 3D Bioreactor Centerpiece with Minimal HUD */}
          <div className="lg:col-span-6 relative h-[480px] sm:h-[540px] rounded-[12px] sb-surface overflow-hidden">
            <BioreactorScene
              rpm={rpm}
              aerationVvm={aerationVvm}
              scrollProgress={scrollProgress}
              interactive
            />

            {/* Floating Scientific Callout: Top Left */}
            <div className="absolute top-4 left-4 px-3.5 py-2.5 rounded-lg sb-glass pointer-events-none">
              <div className="flex items-center gap-2 text-[11px] font-medium text-[#A1A1AA]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
                <span>Broth Vitality · Simulated</span>
              </div>
              <div className="mt-1 flex items-baseline gap-3 text-[12px] font-mono sb-tabular">
                <span className="text-[#FAFAFA] font-medium">36.8 °C</span>
                <span className="text-[#A1A1AA]">pH 7.05</span>
                <span className="text-[#10B981]">dO₂ 40.5%</span>
              </div>
            </div>

            {/* Floating Scientific Callout: Top Right */}
            <div className="absolute top-4 right-4 px-2.5 py-1 rounded-md sb-glass text-[11px] font-medium text-[#A1A1AA] pointer-events-none">
              Drag to orbit · 150 L SUB
            </div>

            {/* Floating Scientific Callout: Bottom */}
            <div className="absolute bottom-4 inset-x-4 flex flex-wrap items-center justify-between gap-2 px-3.5 py-2.5 rounded-lg sb-glass text-[12px] pointer-events-none">
              <span className="text-[#A1A1AA]">
                Impeller:{" "}
                <strong className="font-mono font-medium text-[#FAFAFA]">{rpm} rpm</strong>{" "}
                · Gas sparge:{" "}
                <strong className="font-mono font-medium text-[#FAFAFA]">
                  {aerationVvm.toFixed(2)} vvm
                </strong>
              </span>
              <span className="text-[#71717A] capitalize">
                Regime: <strong className="font-medium text-[#FAFAFA]">{liveMetrics.regime}</strong>
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. SCALE PHYSICS & PLATFORM SOLUTION */}
      <section id="challenge" className="py-24 border-t border-[#18181B]">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div>
            <span className="text-[12px] font-semibold text-[#10B981] block">
              Scale Physics
            </span>
            <h2 className="mt-3 text-[32px] sm:text-[40px] font-semibold leading-[1.15] tracking-[-0.03em] text-[#FAFAFA] max-w-[680px]">
              Lab success breaks when vessel geometry changes.
            </h2>
            <p className="mt-4 text-[14px] text-[#A1A1AA] leading-[1.6] max-w-[680px]">
              Moving a fermentation process from a 2 L benchtop reactor to 200 L pilot or 2,000 L GMP tanks cannot preserve power density, tip speed, oxygen transfer, and mixing time simultaneously. ScaleBridge makes every trade-off explicit before a single liter is inoculated.
            </p>
          </div>

          <div className="rounded-[12px] border border-[#27272A] bg-[#111114] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[#27272A] overflow-hidden">
            {[
              {
                icon: Gauge,
                tag: "Hydrodynamics & Shear",
                title: "Coupled P/V vs. Tip Speed",
                body: "Calculates exact shaft power density, Rushton/hydrofoil tip velocities, and turbulent Reynolds regimes across non-similar vessel geometries using Pint-verified dimensional units.",
              },
              {
                icon: Activity,
                tag: "Mass & Heat Transfer",
                title: "OTR Bottlenecks & Evidence Gaps",
                body: "Evaluates Van't Riet kLa predictions against metabolic oxygen demand while explicitly halting and flagging missing broth rheology or cooling jacket measurements.",
              },
              {
                icon: ShieldCheck,
                tag: "Audit-Ready Transfer",
                title: "Explainable Risk & Validation Plans",
                body: "Translates hardware shortfalls and kinetic anomalies into prioritized pre-transfer experiments, reviewer sign-offs, and provenance-hashed transfer dossiers.",
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="p-7 transition-colors hover:bg-[#16161A]"
                >
                  <div className="flex items-center justify-between">
                    <Icon className="w-4 h-4 text-[#A1A1AA]" />
                    <span className="text-[12px] font-medium text-[#71717A]">
                      {item.tag}
                    </span>
                  </div>
                  <h3 className="mt-8 text-[16px] font-semibold leading-[1.4] text-[#FAFAFA]">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-[14px] font-normal leading-[1.6] text-[#A1A1AA]">
                    {item.body}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 3. INTERACTIVE DIGITAL TWIN TELEMETRY & DATA VISUALIZATION */}
      <section id="telemetry" className="py-24 border-t border-[#18181B]">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <span className="text-[12px] font-semibold text-[#10B981] block">
                Real-Time Telemetry
              </span>
              <h2 className="mt-3 text-[32px] sm:text-[40px] font-semibold leading-[1.15] tracking-[-0.03em] text-[#FAFAFA] max-w-[680px]">
                Observe biology, hydrodynamics, and nutrient kinetics together.
              </h2>
            </div>
            <Link
              href="/dashboard"
              className="text-[13px] font-medium text-[#FAFAFA] hover:text-[#A1A1AA] inline-flex items-center gap-1.5 transition-colors shrink-0"
            >
              <span>Launch full analytics workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
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

      {/* 4. UNIFIED ECOSYSTEM ARCHITECTURE (CONNECTED 4-COLUMN BENTO) */}
      <section id="ecosystem" className="py-24 border-t border-[#18181B]">
        <div className="max-w-7xl mx-auto px-6 space-y-12">
          <div>
            <span className="text-[12px] font-semibold text-[#A1A1AA] block">
              Unified Architecture
            </span>
            <h2 className="mt-3 text-[32px] sm:text-[40px] font-semibold leading-[1.15] tracking-[-0.03em] text-[#FAFAFA] max-w-[680px]">
              From raw bioreactor logs to verified manufacturing readiness.
            </h2>
          </div>

          <div className="rounded-[12px] border border-[#27272A] bg-[#111114] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-[#27272A] overflow-hidden">
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
                title: "Validation Plan",
                desc: "Prioritized commissioning checks, engineering insights, reviewer sign-offs, and PDF transfer reports.",
              },
            ].map((node) => {
              const Icon = node.icon;
              return (
                <div
                  key={node.step}
                  className="p-7 transition-colors hover:bg-[#16161A]"
                >
                  <div className="flex items-center justify-between">
                    <Icon className="w-4 h-4 text-[#A1A1AA]" />
                    <span className="font-mono text-[12px] text-[#71717A]">
                      {node.step}
                    </span>
                  </div>
                  <h3 className="mt-8 text-[16px] font-semibold leading-[1.4] text-[#FAFAFA]">
                    {node.title}
                  </h3>
                  <p className="mt-2 text-[14px] font-normal leading-[1.6] text-[#A1A1AA]">
                    {node.desc}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Closing CTA Banner */}
          <div className="rounded-[12px] sb-cta-glow px-8 py-9 sm:px-10 sm:py-9 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <span className="text-[12px] font-semibold text-[#10B981] block">
                Biotechnology Control Center
              </span>
              <h3 className="mt-1.5 text-[24px] font-semibold tracking-[-0.02em] leading-[1.3] text-[#FAFAFA]">
                Enter the ScaleBridge Engineering Workspace
              </h3>
              <p className="mt-1.5 text-[14px] text-[#A1A1AA] leading-[1.6] max-w-xl">
                Explore live or simulated CHO fed-batch telemetry, compare 2 L to 2,000 L bioreactors, run deterministic scale-up assessments, and inspect validation plans.
              </p>
            </div>
            <Link
              href="/dashboard"
              className="shrink-0 inline-flex items-center justify-center gap-2 h-10 px-5 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
            >
              <span>Launch Control Center</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#18181B] py-7 px-6 text-[12px] text-[#71717A]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span>ScaleBridge.bio — Deterministic Bioprocess Intelligence</span>
          <span>Landing telemetry labeled as simulated or sample data</span>
        </div>
      </footer>
    </div>
  );
}
