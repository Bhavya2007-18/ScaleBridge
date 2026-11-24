"use client";

import React, { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Cpu,
  Database,
  FileText,
  FlaskConical,
  Gauge,
  Layers,
  LogIn,
  LogOut,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import {
  apiFetch,
  AssessmentRecord,
  BatchRecord,
  clearStoredAuth,
  DataChecklistResponse,
  getReportDownloadUrl,
  getStoredAuth,
  MeasurementSeries,
  Project,
  QualityReport,
  setStoredAuth,
  UserProfile,
  VesselRecord,
} from "@/lib/api";
import {
  computeScaleUpPreview,
  DataOrigin,
  SAMPLE_AI_INSIGHTS,
  SAMPLE_ASSESSMENT,
  SAMPLE_BATCHES,
  SAMPLE_BIOPROCESS_SERIES,
  SAMPLE_CHECKLIST,
  SAMPLE_PROJECTS,
  SAMPLE_VESSELS,
} from "@/lib/mockBioprocess";
import {
  CalculationTraceCard,
  CompatBadge,
  DataOriginBadge,
  formatQuantity,
  NatureBadge,
  SeverityBadge,
} from "@/components/ScientificBadges";
import { BatchOverlaySeries, BatchTrendChart } from "@/components/BatchTrendChart";
import { ColumnMapper, ColumnMappingEntry } from "@/components/ColumnMapper";
import { VesselCompareTable } from "@/components/VesselCompareTable";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { BioprocessCharts } from "@/components/dashboard/BioprocessCharts";
import { ScientificLoader } from "@/components/dashboard/ScientificLoader";
import { SYNTHETIC_GOLDEN_CSV } from "@/lib/format";

function parseCsvTextToPreview(csvText: string): {
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

const BioreactorScene = dynamic(
  () => import("@/components/three/BioreactorScene").then((m) => m.BioreactorScene),
  {
    ssr: false,
    loading: () => <ScientificLoader compact label="Loading Digital Twin..." />,
  }
);

type NavSection =
  | "overview"
  | "passport"
  | "ingestion"
  | "vessels"
  | "modeler"
  | "readiness";

const NAV_ITEMS: Array<{ id: NavSection; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: "overview", label: "Control Overview", icon: Activity },
  { id: "passport", label: "Process Passport", icon: FlaskConical },
  { id: "ingestion", label: "Data Ingestion", icon: Database },
  { id: "vessels", label: "Vessel Fleet", icon: Layers },
  { id: "modeler", label: "Scale-Up Modeler", icon: Gauge },
  { id: "readiness", label: "Readiness & AI Insights", icon: ShieldCheck },
];

export default function ScaleBridgeControlCenterPage() {
  const [activeNav, setActiveNav] = useState<NavSection>("overview");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [dataOrigin, setDataOrigin] = useState<DataOrigin>("simulated");
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Auth form state
  const [loginEmail, setLoginEmail] = useState("scientist@scalebridge.bio");
  const [loginPassword, setLoginPassword] = useState("ScaleBridge2026!");
  const [authError, setAuthError] = useState<string | null>(null);

  // Workspace domain state (initialized with rich simulated/sample datasets)
  const [projects, setProjects] = useState<Project[]>(SAMPLE_PROJECTS);
  const [selectedProject, setSelectedProject] = useState<Project>(SAMPLE_PROJECTS[0]);
  const [checklist, setChecklist] = useState<DataChecklistResponse>(SAMPLE_CHECKLIST);
  const [batches, setBatches] = useState<BatchRecord[]>(SAMPLE_BATCHES);
  const [vessels, setVessels] = useState<VesselRecord[]>(SAMPLE_VESSELS);
  const [assessment, setAssessment] = useState<AssessmentRecord>(SAMPLE_ASSESSMENT);
  const [overlaySeries, setOverlaySeries] = useState<BatchOverlaySeries[]>([]);

  const [statusBanner, setStatusBanner] = useState<string | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState<boolean>(false);

  // Interactive Digital Twin controls
  const [twinRpm, setTwinRpm] = useState<number>(185);
  const [twinVvm, setTwinVvm] = useState<number>(0.65);

  // Passport update form state
  const [recipeVersion, setRecipeVersion] = useState("R-2026.3");
  const [densityVal, setDensityVal] = useState(1025);
  const [viscosityVal, setViscosityVal] = useState(1.4);
  const [cStarVal, setCStarVal] = useState(0.21);

  // Ingestion form state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadRunCode, setUploadRunCode] = useState("LAB-2L-RUN-03");
  const [uploadVolume, setUploadVolume] = useState(2.0);
  const [lastQualityReport, setLastQualityReport] = useState<QualityReport | null>(null);
  const [csvHeaders, setCsvHeaders] = useState<string[]>(
    () => parseCsvTextToPreview(SYNTHETIC_GOLDEN_CSV).headers
  );
  const [csvSampleRows, setCsvSampleRows] = useState<
    Array<Record<string, string | number | null>>
  >(() => parseCsvTextToPreview(SYNTHETIC_GOLDEN_CSV).rows);

  // Vessel registration form state
  const [showNewVesselForm, setShowNewVesselForm] = useState(false);
  const [newVesselName, setNewVesselName] = useState("BioFlo 500L Pilot Stainless");
  const [newVesselScale, setNewVesselScale] = useState<"lab" | "pilot" | "production">("pilot");
  const [newVesselVolMax, setNewVesselVolMax] = useState(500);
  const [newVesselImpellerD, setNewVesselImpellerD] = useState(0.36);
  const [newVesselMaxRpm, setNewVesselMaxRpm] = useState(210);
  const [newVesselMaxPower, setNewVesselMaxPower] = useState(5200);
  const [newVesselMaxVvm, setNewVesselMaxVvm] = useState(0.95);
  const [newVesselImpellerType, setNewVesselImpellerType] = useState("2x Rushton + Hydrofoil");

  // Scenario Modeler state
  const [sourceVesselId, setSourceVesselId] = useState<string>(SAMPLE_VESSELS[0].id);
  const [targetVesselId, setTargetVesselId] = useState<string>(SAMPLE_VESSELS[1].id);
  const [targetVolumeL, setTargetVolumeL] = useState<number>(150);
  const [targetRpm, setTargetRpm] = useState<number>(145);
  const [aerationVvm, setAerationVvm] = useState<number>(0.6);
  const [primaryCrit, setPrimaryCrit] = useState<"S-PV" | "S-TIP">("S-PV");

  // Reviewer sign-off state
  const [reviewDecision, setReviewDecision] = useState<"approved_for_discussion" | "changes_requested">(
    "approved_for_discussion"
  );
  const [reviewComment, setReviewComment] = useState(
    "Verified deterministic P/V, tip speed, and kLa calculations. Dynamic gassing-out kLa measurement scheduled for 150 L SUB commissioning."
  );

  useEffect(() => {
    const stored = getStoredAuth();
    if (stored.token && stored.user) {
      setUser(stored.user);
      if (stored.token !== "mock_demo_token") {
        void attemptLiveSync();
      }
    }
  }, []);

  async function attemptLiveSync() {
    try {
      const [projResp, vesResp] = await Promise.all([
        apiFetch<{ items: Project[] }>("/projects"),
        apiFetch<{ items: VesselRecord[] }>("/vessels"),
      ]);
      if (projResp.items.length > 0) {
        setProjects(projResp.items);
        setSelectedProject(projResp.items[0]);
        setDataOrigin("live");
        await selectLiveProject(projResp.items[0]);
      }
      if (vesResp.items.length > 0) {
        setVessels(vesResp.items);
        setSourceVesselId(vesResp.items[0].id);
        if (vesResp.items[1]) setTargetVesselId(vesResp.items[1].id);
      }
    } catch {
      // Backend offline or unauthenticated: remain cleanly in Simulated Demo mode
      setDataOrigin("simulated");
    }
  }

  async function selectLiveProject(proj: Project) {
    setSelectedProject(proj);
    if (dataOrigin !== "live") return;
    try {
      const [chk, batchResp, scenResp] = await Promise.all([
        apiFetch<DataChecklistResponse>(`/projects/${proj.id}/data-checklist`),
        apiFetch<{ items: BatchRecord[] }>(`/projects/${proj.id}/batches`),
        apiFetch<{ items: Array<Record<string, unknown>> }>(`/projects/${proj.id}/scenarios`),
      ]);
      setChecklist(chk);
      setBatches(batchResp.items);

      const seriesList: BatchOverlaySeries[] = [];
      for (const b of batchResp.items.slice(0, 2)) {
        const m = await apiFetch<{ run_code: string; series: MeasurementSeries[] }>(
          `/batches/${b.id}/measurements`
        );
        seriesList.push({ batchRunCode: m.run_code, series: m.series });
      }
      setOverlaySeries(seriesList);

      const firstScenWithAssess = scenResp.items.find((s) => s.latest_assessment_id);
      if (firstScenWithAssess && typeof firstScenWithAssess.latest_assessment_id === "string") {
        const a = await apiFetch<AssessmentRecord>(
          `/assessments/${firstScenWithAssess.latest_assessment_id}`
        );
        setAssessment(a);
      }
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to load live project data");
    }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setAuthError(null);
    setBusy(true);
    try {
      const resp = await apiFetch<{ access_token: string; user: UserProfile }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const orgId = resp.user.memberships[0]?.organization_id || "";
      setStoredAuth(resp.access_token, orgId, resp.user);
      setUser(resp.user);
      setShowAuthModal(false);
      setStatusBanner(`Authenticated live session as ${resp.user.full_name}`);
      await attemptLiveSync();
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Backend unreachable or invalid credentials");
    } finally {
      setBusy(false);
    }
  }

  function handleGuestDemoMode() {
    const demoUser: UserProfile = {
      id: "usr_mock_demo_01",
      email: "scientist@scalebridge.bio",
      full_name: "Dr. Elena Vance (Demo Scientist)",
      memberships: [
        {
          organization_id: "org_mock_demo_01",
          name: "ScaleBridge Bio Demo Org",
          slug: "scalebridge-demo",
          role: "scientist",
        },
      ],
    };
    setUser(demoUser);
    setStoredAuth("mock_demo_token", "org_mock_demo_01", demoUser);
    setDataOrigin("simulated");
    setShowAuthModal(false);
    setStatusBanner("Active in Simulated Digital-Twin Mode (offline deterministic workspace).");
  }

  function handleLogout() {
    clearStoredAuth();
    setUser(null);
    setDataOrigin("simulated");
  }

  // Deterministic live preview for Scale-Up Modeler
  const sourceVessel = vessels.find((v) => v.id === sourceVesselId) || vessels[0];
  const targetVessel = vessels.find((v) => v.id === targetVesselId) || vessels[1] || vessels[0];

  const modelPreview = useMemo(() => {
    const srcVol = sourceVessel?.latest_version.parameters.working_volume_max?.value ?? 2.0;
    const srcImp = sourceVessel?.latest_version.parameters.impeller_diameter?.value ?? 0.055;
    const tgtImp = targetVessel?.latest_version.parameters.impeller_diameter?.value ?? 0.24;
    return computeScaleUpPreview({
      sourceVolumeL: srcVol,
      sourceRpm: 420,
      sourceImpellerM: srcImp,
      targetVolumeL,
      targetRpm,
      targetImpellerM: tgtImp,
      aerationVvm,
      densityKgM3: densityVal,
      viscosityPaS: viscosityVal / 1000,
    });
  }, [sourceVessel, targetVessel, targetVolumeL, targetRpm, aerationVvm, densityVal, viscosityVal]);

  async function handleSavePassportVersion(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrorBanner(null);
    try {
      if (dataOrigin === "live") {
        await apiFetch(`/projects/${selectedProject.id}/passport-versions`, {
          method: "POST",
          body: JSON.stringify({
            recipe_version: recipeVersion,
            process_description:
              selectedProject.latest_passport?.process_description ||
              "Aerobic fed-batch fermentation passport",
            organism_context: selectedProject.latest_passport?.organism_context || {},
            medium_context: {
              name: "Defined Mineral Salts + Glucose Feed",
              density: { value: densityVal, unit: "kg/m^3", provenance: "user_assumption", value_nature: "assumed" },
              viscosity: { value: viscosityVal, unit: "mPa*s", provenance: "user_assumption", value_nature: "assumed" },
              oxygen_saturation_concentration: { value: cStarVal, unit: "mmol/L", provenance: "user_assumption", value_nature: "assumed" },
            },
            process_parameters: selectedProject.latest_passport?.process_parameters || [],
            change_note: `Updated medium properties (${recipeVersion})`,
          }),
        });
        const updatedProj = await apiFetch<Project>(`/projects/${selectedProject.id}`);
        await selectLiveProject(updatedProj);
      } else {
        setSelectedProject((prev) => ({
          ...prev,
          latest_passport: prev.latest_passport
            ? {
                ...prev.latest_passport,
                version: prev.latest_passport.version + 1,
                recipe_version: recipeVersion,
                medium_context: {
                  ...prev.latest_passport.medium_context,
                  density: { value: densityVal, unit: "kg/m^3", provenance: "user_assumption", value_nature: "assumed" },
                  viscosity: { value: viscosityVal, unit: "mPa*s", provenance: "user_assumption", value_nature: "assumed" },
                  oxygen_saturation_concentration: { value: cStarVal, unit: "mmol/L", provenance: "user_assumption", value_nature: "assumed" },
                },
              }
            : null,
        }));
      }
      setStatusBanner(`Saved immutable Process Passport (${recipeVersion}).`);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to save passport version");
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadAndImportBatch(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile) return;
    setBusy(true);
    setErrorBanner(null);
    try {
      if (dataOrigin === "live") {
        const fd = new FormData();
        fd.append("file", uploadFile);
        const uploaded = await apiFetch<{ file_id: string }>("/uploads", { method: "POST", body: fd });
        const batchResp = await apiFetch<{ batch_id: string; quality_report: QualityReport }>(
          `/projects/${selectedProject.id}/batches`,
          {
            method: "POST",
            body: JSON.stringify({
              file_id: uploaded.file_id,
              run_code: uploadRunCode,
              scale_label: "2 L Benchtop",
              working_volume_value: uploadVolume,
              working_volume_unit: "L",
              source_vessel_version_id: sourceVessel.latest_version.id,
            }),
          }
        );
        setLastQualityReport(batchResp.quality_report);
        await selectLiveProject(selectedProject);
      } else {
        const text = await uploadFile.slice(0, 4096).text();
        const rows = Math.max(1, text.split("\n").length - 1);
        const newBatch: BatchRecord = {
          id: `batch_local_${Date.now()}`,
          project_id: selectedProject.id,
          run_code: uploadRunCode,
          scale_label: `${uploadVolume} L Benchtop`,
          working_volume_original: uploadVolume,
          working_volume_unit: "L",
          working_volume_si: uploadVolume / 1000,
          start_time: new Date().toISOString(),
          end_time: null,
          operator: user?.full_name || "Demo Scientist",
          notes: `Locally validated CSV (${uploadFile.name})`,
          is_synthetic: true,
          variables_available: ["temperature", "ph", "dissolved_oxygen", "agitation_rpm"],
          summary: {},
          created_at: new Date().toISOString(),
        };
        setBatches((prev) => [newBatch, ...prev]);
        setLastQualityReport({
          file_id: "local_csv_preview",
          rows_total: rows,
          rows_imported: rows,
          variables: [
            {
              variable: "dissolved_oxygen",
              unit_original: "%",
              unit_si: "percent",
              unit_display: "%sat",
              count: rows,
              valid_count: rows,
              missing_count: 0,
              invalid_count: 0,
              min_display: 38.4,
              max_display: 99.1,
            },
          ],
          issues: [],
          conversions: [{ variable: "working_volume", from_unit: "L", to_unit: "m^3", method: "pint", pint_version: "0.24" }],
          blocking: false,
        });
      }
      setStatusBanner(`Ingested and validated batch ${uploadRunCode}.`);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Batch ingestion failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleRunScaleUpAssessment() {
    setBusy(true);
    setErrorBanner(null);
    try {
      if (dataOrigin === "live") {
        const scen = await apiFetch<{ id: string }>(`/projects/${selectedProject.id}/scenarios`, {
          method: "POST",
          body: JSON.stringify({
            name: `${sourceVessel.name} → ${targetVessel.name}`,
            source_vessel_version_id: sourceVessel.latest_version.id,
            target_vessel_version_id: targetVessel.latest_version.id,
            target_working_volume: {
              value: targetVolumeL,
              unit: "L",
              provenance: "user_assumption",
              value_nature: "assumed",
            },
            primary_criterion: primaryCrit,
            selected_criteria: ["S-PV", "S-TIP", "S-VVM"],
          }),
        });
        const res = await apiFetch<AssessmentRecord>(`/scenarios/${scen.id}/run-assessment`, {
          method: "POST",
        });
        setAssessment(res);
      } else {
        // Update deterministic preview assessment
        setTwinRpm(targetRpm);
        setTwinVvm(aerationVvm);
        setAssessment((prev) => ({
          ...prev,
          id: `assess_${Date.now()}`,
          calculations: [
            {
              ...prev.calculations[0],
              output: { value: modelPreview.targetPvWm3, unit: "W/m^3", provenance: "calculated", value_nature: "calculated" },
            },
            {
              ...prev.calculations[1],
              output: { value: modelPreview.targetTipSpeedMs, unit: "m/s", provenance: "calculated", value_nature: "calculated" },
            },
            {
              ...prev.calculations[2],
              output: { value: modelPreview.targetKlaPerH, unit: "1/h", provenance: "published_correlation", value_nature: "estimated" },
            },
          ],
          created_at: new Date().toISOString(),
        }));
      }
      setActiveNav("readiness");
      setStatusBanner("Executed deterministic scale-up assessment and updated risk register.");
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Assessment run failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateTaskStatus(taskId: string, newStatus: "open" | "in_progress" | "done" | "waived") {
    let waivedReason: string | null = null;
    if (newStatus === "waived") {
      waivedReason = window.prompt("Enter mandatory engineering justification for waiving this task:");
      if (!waivedReason || !waivedReason.trim()) return;
    }
    if (dataOrigin === "live") {
      await apiFetch(`/validation-tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus, waived_reason: waivedReason }),
      });
      const refreshed = await apiFetch<AssessmentRecord>(`/assessments/${assessment.id}`);
      setAssessment(refreshed);
    } else {
      setAssessment((prev) => ({
        ...prev,
        validation_tasks: prev.validation_tasks.map((t) =>
          t.id === taskId ? { ...t, status: newStatus, waived_reason: waivedReason } : t
        ),
      }));
    }
  }

  async function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault();
    if (dataOrigin === "live") {
      try {
        await apiFetch(`/assessments/${assessment.id}/reviews`, {
          method: "POST",
          body: JSON.stringify({ decision: reviewDecision, comment: reviewComment }),
        });
        const refreshed = await apiFetch<AssessmentRecord>(`/assessments/${assessment.id}`);
        setAssessment(refreshed);
        setStatusBanner("Recorded domain-expert sign-off on live ledger.");
      } catch (err) {
        setErrorBanner(err instanceof Error ? err.message : "Sign-off failed");
      }
    } else {
      setAssessment((prev) => ({
        ...prev,
        reviews: [
          {
            id: `rev_${Date.now()}`,
            reviewer_name: user?.full_name || "Lead Bioprocess Reviewer",
            decision: reviewDecision,
            comment: reviewComment,
            created_at: new Date().toISOString(),
          },
          ...prev.reviews,
        ],
      }));
      setStatusBanner("Recorded sign-off in simulated demonstration assessment.");
    }
  }

  async function handleExportReport() {
    if (dataOrigin === "live") {
      try {
        const rep = await apiFetch<{ id: string; version: number }>(
          `/assessments/${assessment.id}/reports`,
          { method: "POST" }
        );
        const { token, orgId } = getStoredAuth();
        const res = await fetch(getReportDownloadUrl(rep.id), {
          headers: { Authorization: `Bearer ${token || ""}`, "X-Organization-Id": orgId || "" },
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `ScaleBridge_Transfer_Report_v${rep.version}.pdf`;
          a.click();
          window.URL.revokeObjectURL(url);
        }
      } catch (err) {
        setErrorBanner(err instanceof Error ? err.message : "PDF export failed");
      }
    } else {
      window.print();
    }
  }

  const latestPoint = SAMPLE_BIOPROCESS_SERIES[SAMPLE_BIOPROCESS_SERIES.length - 1];

  return (
    <div className="min-h-screen bg-[#09090B] text-[#FAFAFA] flex">
      {/* LEFT SIDEBAR */}
      <aside className="hidden lg:flex w-64 shrink-0 flex-col justify-between bg-[#09090B] border-r border-[#18181B] p-5 sticky top-0 h-screen">
        <div className="space-y-8">
          {/* Brand */}
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-7 h-7 rounded-md bg-[#111114] border border-[#27272A] flex items-center justify-center shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]">
                <span className="w-2 h-2 rounded-full bg-[#10B981]" />
              </div>
              <div>
                <span className="font-semibold tracking-[-0.02em] text-[15px] text-[#FAFAFA] block">
                  ScaleBridge<span className="text-[#71717A] font-normal">.bio</span>
                </span>
                <span className="text-[11px] font-medium text-[#71717A] block">
                  Control Center
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="space-y-1">
            <p className="px-3 text-[11px] font-medium text-[#71717A] mb-2">
              Workspace
            </p>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveNav(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                    active
                      ? "bg-[#18181B] text-[#FAFAFA] border border-[#27272A]"
                      : "text-[#A1A1AA] hover:text-[#FAFAFA] hover:bg-[#111114] border border-transparent"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? "text-[#FAFAFA]" : "text-[#71717A]"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Active Vessel Status Card in Sidebar */}
        <div className="space-y-3">
          <div className="p-3.5 rounded-[10px] bg-[#111114] border border-[#27272A] space-y-2 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#71717A] font-medium">Target Digital Twin</span>
              <span className="flex items-center gap-1.5 text-[#10B981] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
                Active
              </span>
            </div>
            <p className="text-[13px] font-semibold text-[#FAFAFA] truncate">
              {targetVessel?.name}
            </p>
            <div className="flex justify-between text-[11px] font-mono text-[#71717A]">
              <span>{twinRpm} rpm</span>
              <span>{twinVvm.toFixed(2)} vvm</span>
            </div>
          </div>

          <Link
            href="/"
            className="flex items-center justify-center gap-2 w-full h-9 rounded-lg border border-[#27272A] bg-[#111114] hover:bg-[#16161A] text-[12px] font-medium text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Overview</span>
          </Link>
        </div>
      </aside>

      {/* MAIN CONTENT SHELL */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* TOP NAVIGATION BAR */}
        <header className="sticky top-0 z-40 h-16 bg-[#09090B]/85 backdrop-blur-md border-b border-[#18181B] px-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0">
            <div className="lg:hidden flex items-center gap-2">
              <Link href="/" className="text-[13px] font-medium text-[#A1A1AA] hover:text-[#FAFAFA]">
                ← Overview
              </Link>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2.5">
                <select
                  value={selectedProject.id}
                  onChange={(e) => {
                    const p = projects.find((pr) => pr.id === e.target.value);
                    if (p) void selectLiveProject(p);
                  }}
                  className="bg-transparent text-[14px] font-semibold tracking-[-0.01em] text-[#FAFAFA] focus:outline-none cursor-pointer truncate"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id} className="bg-[#111114]">
                      {p.name}
                    </option>
                  ))}
                </select>
                <DataOriginBadge origin={dataOrigin} />
              </div>
              <p className="text-[12px] text-[#71717A] truncate">
                {selectedProject.organism_name} · {selectedProject.process_type} ·{" "}
                <span className="font-mono">
                  {selectedProject.latest_passport?.recipe_version || "R-2026.2"}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="hidden sm:block text-right">
                  <div className="text-[13px] font-medium text-[#FAFAFA]">{user.full_name}</div>
                  <div className="text-[11px] font-medium text-[#10B981] capitalize">
                    {user.memberships[0]?.role || "scientist"}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-[#27272A] bg-[#111114] hover:bg-[#16161A] text-[13px] font-medium text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Sign out</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] text-[13px] font-medium transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Connect Live API</span>
              </button>
            )}
          </div>
        </header>

        {/* Mobile Nav Strip */}
        <div className="lg:hidden flex overflow-x-auto gap-1.5 px-4 py-2.5 border-b border-[#18181B] bg-[#09090B]">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-medium whitespace-nowrap ${
                activeNav === item.id
                  ? "bg-[#18181B] text-[#FAFAFA] border border-[#27272A]"
                  : "text-[#A1A1AA]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Status / Error Banners */}
        {(statusBanner || errorBanner) && (
          <div className="px-6 pt-4 space-y-2">
            {statusBanner && (
              <div className="p-3 rounded-lg bg-[#10B981]/10 border border-[#10B981]/25 text-xs font-medium text-[#10B981] flex items-center justify-between">
                <span>{statusBanner}</span>
                <button onClick={() => setStatusBanner(null)} className="text-[#10B981] hover:text-white">
                  ✕
                </button>
              </div>
            )}
            {errorBanner && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-400/35 text-xs font-medium text-rose-200 flex items-center justify-between">
                <span>{errorBanner}</span>
                <button onClick={() => setErrorBanner(null)} className="text-rose-400 hover:text-white">
                  ✕
                </button>
              </div>
            )}
          </div>
        )}

        {/* MAIN WORKSPACE BODY */}
        <main className="flex-1 p-6 space-y-6 max-w-[1440px] w-full mx-auto">
          {/* 1. CONTROL OVERVIEW */}
          {activeNav === "overview" && (
            <div className="space-y-6">
              {/* Top KPI Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                <KpiCard
                  label="Temperature"
                  value={latestPoint.temperatureC}
                  decimals={1}
                  unit="°C"
                  delta="Setpoint 36.8 °C"
                  status="nominal"
                  sparkline={SAMPLE_BIOPROCESS_SERIES.map((p) => p.temperatureC)}
                  origin={dataOrigin}
                />
                <KpiCard
                  label="Broth pH"
                  value={latestPoint.ph}
                  decimals={2}
                  unit="pH"
                  delta="Deadband ±0.05"
                  status="nominal"
                  sparkline={SAMPLE_BIOPROCESS_SERIES.map((p) => p.ph)}
                  origin={dataOrigin}
                />
                <KpiCard
                  label="Dissolved O₂"
                  value={latestPoint.dissolvedOxygenPct}
                  decimals={1}
                  unit="%sat"
                  delta="Target ≥ 40.0%"
                  status="nominal"
                  sparkline={SAMPLE_BIOPROCESS_SERIES.map((p) => p.dissolvedOxygenPct)}
                  origin={dataOrigin}
                />
                <KpiCard
                  label="Agitation"
                  value={twinRpm}
                  decimals={0}
                  unit="rpm"
                  delta={`Tip ${(modelPreview.targetTipSpeedMs).toFixed(2)} m/s`}
                  status={modelPreview.shearStatus === "critical" ? "critical" : "nominal"}
                  sparkline={SAMPLE_BIOPROCESS_SERIES.map((p) => p.agitationRpm)}
                  origin={dataOrigin}
                />
                <KpiCard
                  label="Harvest Titer"
                  value={latestPoint.titerGL}
                  decimals={2}
                  unit="g/L"
                  delta="Target ≥ 3.50 g/L"
                  status="nominal"
                  sparkline={SAMPLE_BIOPROCESS_SERIES.map((p) => p.titerGL)}
                  origin={dataOrigin === "live" ? "live" : "sample"}
                />
                <KpiCard
                  label="Efficiency"
                  value={latestPoint.efficiencyPct}
                  decimals={1}
                  unit="%"
                  delta="OTR / OUR Balance"
                  status="nominal"
                  sparkline={SAMPLE_BIOPROCESS_SERIES.map((p) => p.efficiencyPct)}
                  origin={dataOrigin === "live" ? "live" : "simulated"}
                />
              </div>

              {/* Digital Twin + AI Insights Split Row */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Compact Interactive 3D Digital Twin */}
                <div className="lg:col-span-5 sb-surface rounded-[12px] p-5 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <span className="text-[12px] font-semibold text-[#10B981]">
                        Live Reactor Digital Twin
                      </span>
                      <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                        {targetVessel.name}
                      </h3>
                    </div>
                    <DataOriginBadge origin="simulated" />
                  </div>

                  <div className="h-72 rounded-lg bg-[#09090B] border border-[#27272A] overflow-hidden relative">
                    <BioreactorScene rpm={twinRpm} aerationVvm={twinVvm} compact interactive />
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-4 pt-3 border-t border-[#27272A]">
                    <div>
                      <div className="flex justify-between text-[12px] text-[#A1A1AA] mb-1">
                        <span>Impeller Speed</span>
                        <span className="font-mono text-[#FAFAFA]">{twinRpm} rpm</span>
                      </div>
                      <input
                        type="range"
                        min={60}
                        max={240}
                        step={5}
                        value={twinRpm}
                        onChange={(e) => setTwinRpm(Number(e.target.value))}
                        className="w-full accent-[#FAFAFA] cursor-pointer"
                      />
                    </div>
                    <div>
                      <div className="flex justify-between text-[12px] text-[#A1A1AA] mb-1">
                        <span>Sparge VVM</span>
                        <span className="font-mono text-[#10B981]">{twinVvm.toFixed(2)} vvm</span>
                      </div>
                      <input
                        type="range"
                        min={0.15}
                        max={1.2}
                        step={0.05}
                        value={twinVvm}
                        onChange={(e) => setTwinVvm(Number(e.target.value))}
                        className="w-full accent-[#10B981] cursor-pointer"
                      />
                    </div>
                  </div>
                </div>

                {/* AI Optimization Insights & Alerts */}
                <div className="lg:col-span-7 sb-surface rounded-[12px] p-5 flex flex-col justify-between space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[#10B981]" />
                      <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                        Process Optimization &amp; Advisory Insights
                      </h3>
                    </div>
                    <DataOriginBadge origin="simulated" />
                  </div>

                  <div className="space-y-3">
                    {SAMPLE_AI_INSIGHTS.map((ins) => (
                      <div
                        key={ins.id}
                        className="p-4 rounded-lg bg-[#09090B] border border-[#27272A] hover:bg-[#16161A] transition-colors"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-[14px] font-semibold text-[#FAFAFA]">
                            {ins.title}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-mono text-[#10B981] bg-[#10B981]/10 border border-[#10B981]/25 px-2 py-0.5 rounded-full">
                              {ins.impactLabel}
                            </span>
                            <span className="text-[11px] font-mono text-[#71717A]">
                              {ins.confidencePct}% conf.
                            </span>
                          </div>
                        </div>
                        <p className="mt-1.5 text-[13px] text-[#A1A1AA] leading-relaxed">
                          {ins.rationale}
                        </p>
                        <div className="mt-2.5 pt-2 border-t border-[#18181B] text-[12px] text-[#FAFAFA]">
                          <span className="text-[#71717A]">Action: </span>
                          {ins.recommendedAction}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Interactive Bioprocess Charts */}
              <BioprocessCharts data={SAMPLE_BIOPROCESS_SERIES} origin={dataOrigin === "live" ? "live" : "sample"} />

              {/* Bottom Strip: Experiment Batches & Active Alerts */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-7 sb-surface rounded-[12px] p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[15px] font-semibold text-[#FAFAFA]">
                      Experimental &amp; Reference Batches ({batches.length})
                    </h3>
                    <button
                      onClick={() => setActiveNav("ingestion")}
                      className="text-[12px] font-medium text-[#FAFAFA] hover:text-[#A1A1AA]"
                    >
                      + Ingest CSV Batch
                    </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="text-[11px] font-sans font-medium text-[#71717A] border-b border-[#27272A]">
                        <tr>
                          <th className="py-2.5 pr-4">Run Code</th>
                          <th className="py-2.5 pr-4">Scale</th>
                          <th className="py-2.5 pr-4">Volume</th>
                          <th className="py-2.5 pr-4">Operator</th>
                          <th className="py-2.5">Origin</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#18181B] text-[#A1A1AA]">
                        {batches.map((b) => (
                          <tr key={b.id} className="hover:bg-[#16161A]">
                            <td className="py-2.5 pr-4 font-semibold text-[#FAFAFA]">{b.run_code}</td>
                            <td className="py-2.5 pr-4">{b.scale_label || "—"}</td>
                            <td className="py-2.5 pr-4 sb-tabular">
                              {b.working_volume_original ?? "—"} {b.working_volume_unit || ""}
                            </td>
                            <td className="py-2.5 pr-4 text-[#71717A]">{b.operator || "—"}</td>
                            <td className="py-2.5">
                              <DataOriginBadge origin={b.is_synthetic ? "sample" : "live"} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="lg:col-span-5 sb-surface rounded-[12px] p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      <h3 className="text-[15px] font-semibold text-[#FAFAFA]">
                        Process Risk Alerts ({assessment.risk_flags.length})
                      </h3>
                    </div>
                    <button
                      onClick={() => setActiveNav("readiness")}
                      className="text-[12px] font-medium text-[#FAFAFA] hover:text-[#A1A1AA]"
                    >
                      View Readiness →
                    </button>
                  </div>
                  <div className="space-y-2.5">
                    {assessment.risk_flags.slice(0, 3).map((rf) => (
                      <div key={rf.id} className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[13px] font-medium text-[#FAFAFA]">{rf.title}</span>
                          <SeverityBadge severity={rf.severity} outcome={rf.outcome} />
                        </div>
                        <p className="mt-1 text-[12px] text-[#A1A1AA] line-clamp-2">{rf.explanation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 2. PROCESS PASSPORT */}
          {activeNav === "passport" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 sb-surface rounded-[12px] p-6 space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[12px] font-semibold text-[#10B981]">
                      Process Passport · Version {selectedProject.latest_passport?.version ?? 1}
                    </span>
                    <h2 className="text-xl font-semibold tracking-[-0.02em] text-[#FAFAFA] mt-1">
                      {selectedProject.name}
                    </h2>
                  </div>
                  <DataOriginBadge origin={dataOrigin} />
                </div>

                <p className="text-[14px] text-[#A1A1AA] leading-relaxed">
                  {selectedProject.latest_passport?.process_description}
                </p>

                <div className="space-y-2">
                  <h4 className="text-[12px] font-medium text-[#71717A]">
                    Critical Process Parameters (CPPs)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(selectedProject.latest_passport?.process_parameters || []).map((pp) => (
                      <div
                        key={pp.key}
                        className="p-3 rounded-lg bg-[#09090B] border border-[#27272A] flex items-center justify-between"
                      >
                        <div>
                          <span className="text-[11px] text-[#71717A] capitalize block">
                            {pp.key.replace(/_/g, " ")}
                          </span>
                          <span className="text-sm font-mono font-semibold text-[#FAFAFA] sb-tabular">
                            {pp.value} <span className="text-[#71717A] font-normal">{pp.unit}</span>
                          </span>
                        </div>
                        <NatureBadge nature={pp.value_nature} />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2 pt-3 border-t border-[#27272A]">
                  <h4 className="text-[12px] font-medium text-[#71717A]">
                    Required Scale-Up Data Checklist
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {checklist.items.map((it) => (
                      <div
                        key={it.key}
                        className="p-3 rounded-lg bg-[#09090B] border border-[#27272A] flex items-center justify-between text-xs"
                      >
                        <span className="text-[#FAFAFA]">{it.label}</span>
                        <span
                          className={`font-mono text-[10px] uppercase px-2 py-0.5 rounded border ${
                            it.status === "complete"
                              ? "bg-[#10B981]/10 text-[#10B981] border-[#10B981]/25"
                              : it.status === "assumed"
                              ? "bg-amber-500/10 text-amber-300 border-amber-400/25"
                              : "bg-rose-500/10 text-rose-300 border-rose-400/25"
                          }`}
                        >
                          {it.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <form
                onSubmit={handleSavePassportVersion}
                className="lg:col-span-5 sb-surface rounded-[12px] p-6 space-y-4 h-fit"
              >
                <span className="text-[12px] font-semibold text-[#10B981]">
                  Immutable Version Revision
                </span>
                <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                  Update Broth &amp; Medium Properties
                </h3>
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-[#A1A1AA] mb-1">Recipe Version Tag</label>
                    <input
                      value={recipeVersion}
                      onChange={(e) => setRecipeVersion(e.target.value)}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1">Broth Density (kg/m³)</label>
                    <input
                      type="number"
                      value={densityVal}
                      onChange={(e) => setDensityVal(Number(e.target.value))}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1">Dynamic Viscosity (mPa·s)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={viscosityVal}
                      onChange={(e) => setViscosityVal(Number(e.target.value))}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1">O₂ Saturation C* (mmol/L)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={cStarVal}
                      onChange={(e) => setCStarVal(Number(e.target.value))}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={busy}
                  className="w-full h-10 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
                >
                  {busy ? "Committing Revision..." : "Commit New Passport Version"}
                </button>
              </form>
            </div>
          )}

          {/* 3. DATA INGESTION */}
          {activeNav === "ingestion" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <form
                  onSubmit={handleUploadAndImportBatch}
                  className="lg:col-span-5 sb-surface rounded-[12px] p-6 space-y-4"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Upload className="w-4 h-4 text-[#A1A1AA]" />
                      <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                        Ingest Bioreactor Run CSV
                      </h3>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        const parsed = parseCsvTextToPreview(SYNTHETIC_GOLDEN_CSV);
                        setCsvHeaders(parsed.headers);
                        setCsvSampleRows(parsed.rows);
                        setStatusBanner(
                          "Loaded synthetic golden 120 h fed-batch reference CSV into ontology mapper."
                        );
                      }}
                      className="px-2.5 py-1 rounded-md bg-[#09090B] hover:bg-[#16161A] border border-[#27272A] text-[11px] font-medium text-[#FAFAFA]"
                    >
                      Load Golden CSV
                    </button>
                  </div>
                  <p className="text-[13px] text-[#A1A1AA]">
                    Parse vendor telemetry exports with unit preservation and physical bounds checking.
                  </p>
                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="block text-[#A1A1AA] mb-1">Run Code</label>
                      <input
                        value={uploadRunCode}
                        onChange={(e) => setUploadRunCode(e.target.value)}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                      />
                    </div>
                    <div>
                      <label className="block text-[#A1A1AA] mb-1">Working Volume (L)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={uploadVolume}
                        onChange={(e) => setUploadVolume(Number(e.target.value))}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                      />
                    </div>
                    <div>
                      <label className="block text-[#A1A1AA] mb-1">CSV Telemetry File</label>
                      <input
                        type="file"
                        accept=".csv,.txt"
                        onChange={(e) => {
                          const file = e.target.files?.[0] || null;
                          setUploadFile(file);
                          if (file) {
                            const reader = new FileReader();
                            reader.onload = (ev) => {
                              const text = (ev.target?.result as string) || "";
                              const parsed = parseCsvTextToPreview(text);
                              if (parsed.headers.length > 0) {
                                setCsvHeaders(parsed.headers);
                                setCsvSampleRows(parsed.rows);
                              }
                            };
                            reader.readAsText(file);
                          }
                        }}
                        className="w-full text-xs text-[#A1A1AA] file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border file:border-[#27272A] file:bg-[#09090B] file:text-[#FAFAFA] file:font-medium"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={busy || !uploadFile}
                    className="w-full h-10 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] disabled:opacity-40 text-[#09090B] font-medium text-[13px] transition-colors"
                  >
                    Validate &amp; Import Uploaded File
                  </button>
                </form>

                <div className="lg:col-span-7 sb-surface rounded-[12px] p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                      Ingestion Quality Audit
                    </h3>
                    <DataOriginBadge origin={dataOrigin} />
                  </div>
                  {lastQualityReport ? (
                    <div className="space-y-3 text-xs font-mono">
                      <div className="p-3 rounded-lg bg-[#10B981]/10 border border-[#10B981]/25 text-[#10B981]">
                        Imported {lastQualityReport.rows_imported} / {lastQualityReport.rows_total} rows · Blocking errors:{" "}
                        {lastQualityReport.blocking ? "YES" : "NO"} · Pint Conversions:{" "}
                        {lastQualityReport.conversions.length}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {lastQualityReport.variables.map((v) => (
                          <div key={v.variable} className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
                            <div className="text-[#FAFAFA] font-semibold">{v.variable}</div>
                            <div className="text-[#A1A1AA] mt-1">
                              Unit: {v.unit_original} → {v.unit_display} ({v.valid_count} valid)
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-[13px] text-[#A1A1AA]">
                      Review and confirm the interactive column mappings below to generate a Pint unit-conversion and DQ-* quality audit report.
                    </p>
                  )}
                </div>
              </div>

              {csvHeaders.length > 0 && (
                <ColumnMapper
                  headers={csvHeaders}
                  sampleRows={csvSampleRows}
                  onSaveMappings={(
                    mappings: ColumnMappingEntry[],
                    tsCfg,
                    report: QualityReport
                  ) => {
                    const newBatch: BatchRecord = {
                      id: `batch_mapped_${Date.now()}`,
                      project_id: selectedProject.id,
                      run_code: uploadRunCode,
                      scale_label: `${uploadVolume} L Benchtop`,
                      working_volume_original: uploadVolume,
                      working_volume_unit: "L",
                      working_volume_si: uploadVolume / 1000,
                      start_time: new Date().toISOString(),
                      end_time: null,
                      operator: user?.full_name || "Dr. Elena Vance",
                      notes: `Mapped ${mappings.length} ontology variables (${tsCfg.column} [${tsCfg.kind}])`,
                      is_synthetic: true,
                      variables_available: mappings.map((m) => m.standardParameter),
                      summary: {},
                      created_at: new Date().toISOString(),
                    };
                    setBatches((prev) => [newBatch, ...prev]);
                    setLastQualityReport(report);
                    setStatusBanner(
                      `Committed batch ${uploadRunCode} with ${mappings.length} Pint-normalized variables (${report.rows_imported} rows).`
                    );
                  }}
                />
              )}

              {overlaySeries.length > 0 && (
                <BatchTrendChart
                  batches={overlaySeries}
                  selectedVariables={["dissolved_oxygen", "temperature", "ph", "agitation_speed"]}
                />
              )}
            </div>
          )}

          {/* 4. VESSEL FLEET */}
          {activeNav === "vessels" && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <span className="text-[12px] font-semibold text-[#10B981]">
                    Equipment Capability Envelopes
                  </span>
                  <h2 className="text-xl font-semibold tracking-[-0.02em] text-[#FAFAFA] mt-0.5">
                    Bioreactor Fleet &amp; Side-by-Side Geometry Matrix
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNewVesselForm((v) => !v)}
                  className="h-9 px-4 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
                >
                  {showNewVesselForm ? "Cancel" : "+ Register Bioreactor"}
                </button>
              </div>

              {showNewVesselForm && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const created: VesselRecord = {
                      id: `ves_custom_${Date.now()}`,
                      name: newVesselName,
                      scale_class: newVesselScale,
                      manufacturer: "Custom Bioreactor Systems",
                      model: `${newVesselVolMax}L-STR`,
                      location: "Pilot Biomanufacturing Suite",
                      latest_version: {
                        id: `vv_custom_${Date.now()}`,
                        version: 1,
                        impeller_type: newVesselImpellerType,
                        impeller_count: 2,
                        sparger_type: "Ring Sparger",
                        instrumentation: ["pH", "dO2", "PT100", "Off-gas O2/CO2"],
                        controls: ["Cascade Agitation + O2", "Jacket Chiller Loop"],
                        parameters: {
                          working_volume_max: {
                            value: newVesselVolMax,
                            unit: "L",
                            provenance: "vendor_datasheet",
                            value_nature: "measured",
                          },
                          impeller_diameter: {
                            value: newVesselImpellerD,
                            unit: "m",
                            provenance: "vendor_datasheet",
                            value_nature: "measured",
                          },
                          max_agitation_speed: {
                            value: newVesselMaxRpm,
                            unit: "rpm",
                            provenance: "vendor_datasheet",
                            value_nature: "measured",
                          },
                          max_power: {
                            value: newVesselMaxPower,
                            unit: "W",
                            provenance: "vendor_datasheet",
                            value_nature: "measured",
                          },
                          max_aeration: {
                            value: newVesselMaxVvm,
                            unit: "vvm",
                            provenance: "vendor_datasheet",
                            value_nature: "measured",
                          },
                        },
                        kla_evidence: [],
                        mixing_time_evidence: [],
                        change_note: "Registered via Control Center",
                        created_at: new Date().toISOString(),
                      },
                      missing_specifications: [
                        {
                          key: "measured_broth_kla",
                          required_by_formulas: ["F-OTR-001"],
                          required_by_checks: [],
                        },
                      ],
                      created_at: new Date().toISOString(),
                    };
                    setVessels((prev) => [...prev, created]);
                    setTargetVesselId(created.id);
                    setShowNewVesselForm(false);
                    setStatusBanner(`Registered vessel profile '${created.name}' to fleet.`);
                  }}
                  className="sb-surface rounded-[12px] p-6 space-y-4 text-xs"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 font-mono">
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Vessel Name</label>
                      <input
                        value={newVesselName}
                        onChange={(e) => setNewVesselName(e.target.value)}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                        required
                      />
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Scale Class</label>
                      <select
                        value={newVesselScale}
                        onChange={(e) =>
                          setNewVesselScale(e.target.value as "lab" | "pilot" | "production")
                        }
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      >
                        <option value="lab">lab</option>
                        <option value="pilot">pilot</option>
                        <option value="production">production</option>
                      </select>
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Max Working Volume (L)</label>
                      <input
                        type="number"
                        value={newVesselVolMax}
                        onChange={(e) => setNewVesselVolMax(Number(e.target.value))}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      />
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Impeller Diameter D (m)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={newVesselImpellerD}
                        onChange={(e) => setNewVesselImpellerD(Number(e.target.value))}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      />
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Max Agitation (rpm)</label>
                      <input
                        type="number"
                        value={newVesselMaxRpm}
                        onChange={(e) => setNewVesselMaxRpm(Number(e.target.value))}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      />
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Motor Power Limit (W)</label>
                      <input
                        type="number"
                        value={newVesselMaxPower}
                        onChange={(e) => setNewVesselMaxPower(Number(e.target.value))}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      />
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Max Aeration (vvm)</label>
                      <input
                        type="number"
                        step="0.05"
                        value={newVesselMaxVvm}
                        onChange={(e) => setNewVesselMaxVvm(Number(e.target.value))}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      />
                    </div>
                    <div>
                      <label className="block font-sans text-[#A1A1AA] mb-1">Impeller Type</label>
                      <input
                        value={newVesselImpellerType}
                        onChange={(e) => setNewVesselImpellerType(e.target.value)}
                        className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-[#FAFAFA]"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    className="h-9 px-4 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px]"
                  >
                    Save Vessel Profile to Fleet
                  </button>
                </form>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {vessels.map((v) => (
                  <div key={v.id} className="sb-surface rounded-[12px] p-6 space-y-4 hover:bg-[#16161A] transition-colors">
                    <div className="flex items-center justify-between text-xs">
                      <span className="px-2.5 py-0.5 rounded-full bg-[#18181B] border border-[#27272A] text-[#FAFAFA] font-mono uppercase text-[10px]">
                        {v.scale_class}
                      </span>
                      <span className="text-[#71717A]">{v.manufacturer || "Custom"}</span>
                    </div>
                    <div>
                      <h3 className="text-[16px] font-semibold text-[#FAFAFA]">{v.name}</h3>
                      <p className="text-[12px] text-[#71717A] mt-0.5">
                        {v.location || "Biomanufacturing Suite"}
                      </p>
                    </div>
                    <div className="space-y-2 pt-3 border-t border-[#27272A] text-xs font-mono">
                      {Object.entries(v.latest_version.parameters).map(([k, q]) => (
                        <div key={k} className="flex justify-between py-1 border-b border-[#18181B]">
                          <span className="text-[#A1A1AA] font-sans capitalize">{k.replace(/_/g, " ")}</span>
                          <span className="text-[#FAFAFA] sb-tabular">{formatQuantity(q, 3)}</span>
                        </div>
                      ))}
                      <div className="flex justify-between py-1">
                        <span className="text-[#A1A1AA] font-sans">Impeller</span>
                        <span className="text-[#FAFAFA] text-right">{v.latest_version.impeller_type}</span>
                      </div>
                    </div>
                    {v.missing_specifications.length > 0 && (
                      <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-400/25 text-[11px] font-mono text-amber-300">
                        Missing Spec: {v.missing_specifications.map((m) => m.key).join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Side-by-Side Vessel Geometry & Capability Comparison Matrix */}
              {sourceVessel && targetVessel && (
                <div className="space-y-3 pt-2">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                      Compare Source vs. Target Vessel Envelopes
                    </h3>
                    <div className="flex items-center gap-2 text-xs font-mono">
                      <select
                        value={sourceVessel.id}
                        onChange={(e) => setSourceVesselId(e.target.value)}
                        className="rounded-lg bg-[#111114] border border-[#27272A] px-3 py-1.5 text-[#FAFAFA]"
                      >
                        {vessels.map((v) => (
                          <option key={v.id} value={v.id}>
                            Source: {v.name}
                          </option>
                        ))}
                      </select>
                      <span className="text-[#71717A]">→</span>
                      <select
                        value={targetVessel.id}
                        onChange={(e) => setTargetVesselId(e.target.value)}
                        className="rounded-lg bg-[#111114] border border-[#27272A] px-3 py-1.5 text-[#FAFAFA]"
                      >
                        {vessels.map((v) => (
                          <option key={v.id} value={v.id}>
                            Target: {v.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <VesselCompareTable
                    sourceVessel={sourceVessel}
                    targetVessel={targetVessel}
                  />
                </div>
              )}
            </div>
          )}

          {/* 5. SCALE-UP MODELER */}
          {activeNav === "modeler" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 sb-surface rounded-[12px] p-6 space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[12px] font-semibold text-[#10B981]">
                      Deterministic Hydrodynamic Coupling
                    </span>
                    <h2 className="text-xl font-semibold tracking-[-0.02em] text-[#FAFAFA] mt-0.5">
                      Configure Vessel Transfer Scenario
                    </h2>
                  </div>
                  <DataOriginBadge origin={dataOrigin} />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="block text-[#A1A1AA] mb-1.5">Source Vessel</label>
                    <select
                      value={sourceVesselId}
                      onChange={(e) => setSourceVesselId(e.target.value)}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    >
                      {vessels.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1.5">Target Vessel</label>
                    <select
                      value={targetVesselId}
                      onChange={(e) => setTargetVesselId(e.target.value)}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    >
                      {vessels.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1.5">Target Volume (L)</label>
                    <input
                      type="number"
                      value={targetVolumeL}
                      onChange={(e) => setTargetVolumeL(Number(e.target.value))}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1.5">Primary Scale Criterion</label>
                    <select
                      value={primaryCrit}
                      onChange={(e) => setPrimaryCrit(e.target.value as "S-PV" | "S-TIP")}
                      className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA] focus:outline-none focus:border-[#A1A1AA]"
                    >
                      <option value="S-PV">Constant Power per Volume (P/V)</option>
                      <option value="S-TIP">Constant Impeller Tip Speed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1.5">
                      Target Agitation (<span className="font-mono text-[#FAFAFA]">{targetRpm} rpm</span>)
                    </label>
                    <input
                      type="range"
                      min={60}
                      max={260}
                      step={5}
                      value={targetRpm}
                      onChange={(e) => setTargetRpm(Number(e.target.value))}
                      className="w-full accent-[#FAFAFA] cursor-pointer"
                    />
                  </div>
                  <div>
                    <label className="block text-[#A1A1AA] mb-1.5">
                      Sparge Aeration (<span className="font-mono text-[#10B981]">{aerationVvm.toFixed(2)} vvm</span>)
                    </label>
                    <input
                      type="range"
                      min={0.15}
                      max={1.2}
                      step={0.05}
                      value={aerationVvm}
                      onChange={(e) => setAerationVvm(Number(e.target.value))}
                      className="w-full accent-[#10B981] cursor-pointer"
                    />
                  </div>
                </div>

                {/* Live Physics Readouts */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-[#27272A]">
                  <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
                    <span className="text-[11px] text-[#71717A] block">Target P/V</span>
                    <span className="text-base font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
                      {modelPreview.targetPvWm3.toFixed(1)}{" "}
                      <span className="text-[11px] font-mono font-normal text-[#71717A]">W/m³</span>
                    </span>
                  </div>
                  <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
                    <span className="text-[11px] text-[#71717A] block">Tip Speed</span>
                    <span className="text-base font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
                      {modelPreview.targetTipSpeedMs.toFixed(2)}{" "}
                      <span className="text-[11px] font-mono font-normal text-[#71717A]">m/s</span>
                    </span>
                  </div>
                  <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
                    <span className="text-[11px] text-[#71717A] block">Predicted kLa</span>
                    <span className="text-base font-semibold text-[#10B981] sb-tabular mt-0.5 inline-block">
                      {modelPreview.targetKlaPerH.toFixed(1)}{" "}
                      <span className="text-[11px] font-mono font-normal text-[#71717A]">1/h</span>
                    </span>
                  </div>
                  <div className="p-3 rounded-lg bg-[#09090B] border border-[#27272A]">
                    <span className="text-[11px] text-[#71717A] block">Reynolds</span>
                    <span className="text-base font-semibold text-[#FAFAFA] sb-tabular mt-0.5 inline-block">
                      {(modelPreview.targetReynolds / 1000).toFixed(1)}k
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleRunScaleUpAssessment}
                  disabled={busy}
                  className="w-full h-10 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
                >
                  {busy ? "Computing Assessment..." : "Execute Deterministic Scale-Up Assessment →"}
                </button>
              </div>

              <div className="lg:col-span-5 sb-surface rounded-[12px] p-5 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[13px] font-medium text-[#FAFAFA]">Target Vessel Twin Preview</span>
                  <DataOriginBadge origin="simulated" />
                </div>
                <div className="h-80 rounded-lg bg-[#09090B] border border-[#27272A] overflow-hidden">
                  <BioreactorScene rpm={targetRpm} aerationVvm={aerationVvm} compact interactive />
                </div>
                <p className="mt-3 text-[12px] text-[#71717A]">
                  3D impeller velocity and bubble dispersion respond directly to your Target RPM and Aeration VVM sliders.
                </p>
              </div>
            </div>
          )}

          {/* 6. READINESS, VALIDATION & REPORTS */}
          {activeNav === "readiness" && (
            <div className="space-y-6">
              {/* Top Summary & PDF Action */}
              <div className="sb-surface rounded-[12px] p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[12px] font-mono text-[#71717A]">
                      Assessment {assessment.id}
                    </span>
                    <DataOriginBadge origin={assessment.is_synthetic ? "simulated" : "live"} />
                  </div>
                  <h2 className="text-xl font-semibold tracking-[-0.02em] text-[#FAFAFA]">
                    Scale-Up Readiness &amp; Equipment Compatibility
                  </h2>
                </div>
                <button
                  onClick={handleExportReport}
                  className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] shrink-0 transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  <span>Export Transfer Report</span>
                </button>
              </div>

              {/* Calculation Traces */}
              <div className="space-y-3">
                <h3 className="text-[12px] font-medium text-[#71717A]">
                  Traceable Engineering Calculations
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {assessment.calculations.map((calc) => (
                    <CalculationTraceCard key={calc.id} calc={calc} />
                  ))}
                </div>
              </div>

              {/* Equipment Compatibility Checks */}
              <div className="space-y-3">
                <h3 className="text-[12px] font-medium text-[#71717A]">
                  Hardware &amp; Utility Compatibility
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {assessment.compatibility_checks.map((cc) => (
                    <div key={cc.id} className="sb-surface rounded-[12px] p-4 space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[13px] font-semibold text-[#FAFAFA]">{cc.title}</span>
                        <CompatBadge outcome={cc.outcome} />
                      </div>
                      <p className="text-[12px] text-[#A1A1AA]">{cc.explanation}</p>
                      <div className="text-[11px] font-mono text-[#71717A] pt-1">
                        Required:{" "}
                        <span className="text-[#FAFAFA]">
                          {cc.required_display ?? "N/A"} {cc.display_unit}
                        </span>{" "}
                        · Cap:{" "}
                        <span className="text-[#FAFAFA]">
                          {cc.capability_max_display ?? "N/A"} {cc.display_unit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Validation Tasks & Reviewer Sign-Off */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-7 sb-surface rounded-[12px] p-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                    <h3 className="text-[15px] font-semibold text-[#FAFAFA]">
                      Validation &amp; Commissioning Plan
                    </h3>
                  </div>
                  <div className="space-y-2.5">
                    {assessment.validation_tasks.map((vt) => (
                      <div
                        key={vt.id}
                        className="p-3.5 rounded-lg bg-[#09090B] border border-[#27272A] flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#18181B] text-[#FAFAFA] border border-[#27272A]">
                              {vt.priority}
                            </span>
                            <span className="text-[13px] font-medium text-[#FAFAFA]">{vt.title}</span>
                          </div>
                          <p className="mt-1 text-[12px] text-[#A1A1AA]">{vt.description}</p>
                        </div>
                        <select
                          value={vt.status}
                          onChange={(e) =>
                            void handleUpdateTaskStatus(
                              vt.id,
                              e.target.value as "open" | "in_progress" | "done" | "waived"
                            )
                          }
                          className="bg-[#111114] border border-[#27272A] rounded-lg px-2.5 py-1.5 text-xs font-mono text-[#FAFAFA] shrink-0"
                        >
                          <option value="open">OPEN</option>
                          <option value="in_progress">IN PROGRESS</option>
                          <option value="done">DONE</option>
                          <option value="waived">WAIVED</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                <form
                  onSubmit={handleSubmitReview}
                  className="lg:col-span-5 sb-surface rounded-[12px] p-5 space-y-3 h-fit"
                >
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#A1A1AA]" />
                    <h3 className="text-[15px] font-semibold text-[#FAFAFA]">
                      Human Engineering Sign-Off
                    </h3>
                  </div>
                  <select
                    value={reviewDecision}
                    onChange={(e) =>
                      setReviewDecision(
                        e.target.value as "approved_for_discussion" | "changes_requested"
                      )
                    }
                    className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-xs text-[#FAFAFA]"
                  >
                    <option value="approved_for_discussion">
                      Approved for Pilot Facility Discussion
                    </option>
                    <option value="changes_requested">
                      Changes / Additional Measurements Requested
                    </option>
                  </select>
                  <textarea
                    rows={3}
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 text-xs text-[#FAFAFA]"
                  />
                  <button
                    type="submit"
                    className="w-full h-9 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px] transition-colors"
                  >
                    Record Reviewer Sign-Off
                  </button>

                  {assessment.reviews.length > 0 && (
                    <div className="pt-3 border-t border-[#27272A] space-y-2">
                      {assessment.reviews.map((rev) => (
                        <div
                          key={rev.id}
                          className="p-2.5 rounded-lg bg-[#10B981]/10 border border-[#10B981]/25 text-xs"
                        >
                          <div className="font-mono font-semibold text-[#10B981]">
                            {rev.reviewer_name} · {rev.decision.replace(/_/g, " ").toUpperCase()}
                          </div>
                          <p className="text-[#FAFAFA] mt-1 text-[11px]">{rev.comment}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </form>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* AUTHENTICATION MODAL (SUPPORTS LIVE API + SKIP TO DEMO) */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full sb-surface rounded-[12px] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-[16px] font-semibold text-[#FAFAFA]">
                Connect Live Engineering Backend
              </h3>
              <button
                onClick={() => setShowAuthModal(false)}
                className="text-[#71717A] hover:text-[#FAFAFA] text-sm"
              >
                ✕
              </button>
            </div>
            <p className="text-[13px] text-[#A1A1AA]">
              Sign in against the FastAPI server for live Postgres persistence, or continue offline in Simulated Digital Twin mode.
            </p>
            <form onSubmit={handleLogin} className="space-y-3 text-xs">
              <div>
                <label className="block text-[#A1A1AA] mb-1">Email</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA]"
                  required
                />
              </div>
              <div>
                <label className="block text-[#A1A1AA] mb-1">Password</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full rounded-lg bg-[#09090B] border border-[#27272A] px-3 py-2 font-mono text-[#FAFAFA]"
                  required
                />
              </div>
              {authError && (
                <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-400/30 text-rose-300 font-mono">
                  {authError}
                </div>
              )}
              <button
                type="submit"
                disabled={busy}
                className="w-full h-9 rounded-lg bg-[#FAFAFA] hover:bg-[#E4E4E7] text-[#09090B] font-medium text-[13px]"
              >
                {busy ? "Authenticating..." : "Sign in to Live API"}
              </button>
              <button
                type="button"
                onClick={handleGuestDemoMode}
                className="w-full h-9 rounded-lg bg-[#09090B] hover:bg-[#16161A] border border-[#27272A] text-[#A1A1AA] hover:text-[#FAFAFA] font-medium text-[13px]"
              >
                Skip (Use Simulated Twin Mode) →
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
