"use client";

import React, { useEffect, useState } from "react";
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
  CalculationTraceCard,
  CompatBadge,
  formatQuantity,
  NatureBadge,
  ProvenanceBadge,
  SeverityBadge,
} from "@/components/ScientificBadges";
import { BatchOverlaySeries, BatchTrendChart } from "@/components/BatchTrendChart";

type StageTab =
  | "passport"
  | "ingestion"
  | "vessels"
  | "scenarios"
  | "readiness"
  | "validation";

export default function ScaleBridgeWorkspacePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loginEmail, setLoginEmail] = useState("scientist@scalebridge.bio");
  const [loginPassword, setLoginPassword] = useState("ScaleBridge2026!");
  const [authError, setAuthError] = useState<string | null>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [checklist, setChecklist] = useState<DataChecklistResponse | null>(null);
  const [batches, setBatches] = useState<BatchRecord[]>([]);
  const [overlaySeries, setOverlaySeries] = useState<BatchOverlaySeries[]>([]);
  const [vessels, setVessels] = useState<VesselRecord[]>([]);
  const [vesselComparison, setVesselComparison] = useState<Record<string, unknown> | null>(null);
  const [scenarios, setScenarios] = useState<Array<Record<string, unknown>>>([]);
  const [assessment, setAssessment] = useState<AssessmentRecord | null>(null);

  const [activeTab, setActiveTab] = useState<StageTab>("passport");
  const [statusBanner, setStatusBanner] = useState<string | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState<boolean>(false);

  // Passport update form state
  const [recipeVersion, setRecipeVersion] = useState("R-2026.2");
  const [densityVal, setDensityVal] = useState(1025);
  const [viscosityVal, setViscosityVal] = useState(1.4);
  const [cStarVal, setCStarVal] = useState(0.21);

  // Upload wizard state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadRunCode, setUploadRunCode] = useState("LAB-2L-RUN-03");
  const [uploadVolume, setUploadVolume] = useState(2.0);
  const [lastQualityReport, setLastQualityReport] = useState<QualityReport | null>(null);

  // Scenario form state
  const [scenName, setScenName] = useState("2 L Lab → 150 L Pilot (Constant P/V Primary)");
  const [targetVolL, setTargetVolL] = useState(150);
  const [primaryCrit, setPrimaryCrit] = useState<"S-PV" | "S-TIP">("S-PV");
  const [aerationBasis, setAerationBasis] = useState<"S-VVM" | "S-VS">("S-VVM");
  const [minDoReq, setMinDoReq] = useState(20);
  const [maxTipConstraint, setMaxTipConstraint] = useState(2.1);

  // Reviewer sign-off state
  const [reviewDecision, setReviewDecision] = useState<"approved_for_discussion" | "changes_requested">(
    "approved_for_discussion"
  );
  const [reviewComment, setReviewComment] = useState(
    "Reviewed deterministic OTR, P/V, tip speed, and Re calculations. Target vessel broth kLa and jacket cooling capacity must be measured/confirmed prior to pilot run."
  );

  useEffect(() => {
    const stored = getStoredAuth();
    if (stored.token && stored.user) {
      setUser(stored.user);
      void loadInitialWorkspace();
    }
  }, []);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setAuthError(null);
    setBusy(true);
    try {
      const resp = await apiFetch<{
        access_token: string;
        user: UserProfile;
      }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const orgId = resp.user.memberships[0]?.organization_id || "";
      setStoredAuth(resp.access_token, orgId, resp.user);
      setUser(resp.user);
      await loadInitialWorkspace();
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function quickSwitchAccount(email: string) {
    setLoginEmail(email);
    setLoginPassword("ScaleBridge2026!");
    setBusy(true);
    setErrorBanner(null);
    try {
      const resp = await apiFetch<{
        access_token: string;
        user: UserProfile;
      }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password: "ScaleBridge2026!" }),
      });
      const orgId = resp.user.memberships[0]?.organization_id || "";
      setStoredAuth(resp.access_token, orgId, resp.user);
      setUser(resp.user);
      setStatusBanner(`Switched active session to ${resp.user.full_name} (${resp.user.memberships[0]?.role})`);
      await loadInitialWorkspace();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Switch account failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadInitialWorkspace() {
    try {
      const [projResp, vesResp] = await Promise.all([
        apiFetch<{ items: Project[] }>("/projects"),
        apiFetch<{ items: VesselRecord[] }>("/vessels"),
      ]);
      setProjects(projResp.items);
      setVessels(vesResp.items);

      if (vesResp.items.length >= 2) {
        const vA = vesResp.items[0].latest_version.id;
        const vB = vesResp.items[1].latest_version.id;
        const cmp = await apiFetch<Record<string, unknown>>(`/vessels/compare?a=${vA}&b=${vB}`);
        setVesselComparison(cmp);
      }

      if (projResp.items.length > 0) {
        await selectProject(projResp.items[0]);
      }
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to load workspace");
    }
  }

  async function selectProject(proj: Project) {
    setSelectedProject(proj);
    const [chk, batchResp, scenResp] = await Promise.all([
      apiFetch<DataChecklistResponse>(`/projects/${proj.id}/data-checklist`),
      apiFetch<{ items: BatchRecord[] }>(`/projects/${proj.id}/batches`),
      apiFetch<{ items: Array<Record<string, unknown>> }>(`/projects/${proj.id}/scenarios`),
    ]);
    setChecklist(chk);
    setBatches(batchResp.items);
    setScenarios(scenResp.items);

    // Load measurement series for up to 2 batches for comparison
    const seriesList: BatchOverlaySeries[] = [];
    for (const b of batchResp.items.slice(0, 2)) {
      const m = await apiFetch<{ run_code: string; series: MeasurementSeries[] }>(
        `/batches/${b.id}/measurements`
      );
      seriesList.push({ batchRunCode: m.run_code, series: m.series });
    }
    setOverlaySeries(seriesList);

    // Load latest assessment if any scenario exists
    const firstScenWithAssess = scenResp.items.find((s) => s.latest_assessment_id);
    if (firstScenWithAssess && typeof firstScenWithAssess.latest_assessment_id === "string") {
      const a = await apiFetch<AssessmentRecord>(
        `/assessments/${firstScenWithAssess.latest_assessment_id}`
      );
      setAssessment(a);
    }
  }

  async function handleSavePassportVersion(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProject) return;
    setBusy(true);
    setErrorBanner(null);
    try {
      await apiFetch(`/projects/${selectedProject.id}/passport-versions`, {
        method: "POST",
        body: JSON.stringify({
          recipe_version: recipeVersion,
          process_description:
            selectedProject.latest_passport?.process_description ||
            "Aerobic microbial fed-batch fermentation process passport",
          organism_context: selectedProject.latest_passport?.organism_context || {},
          medium_context: {
            name: "Defined Mineral Salts + Glucose Feed",
            density: {
              value: densityVal,
              unit: "kg/m^3",
              provenance: "user_assumption",
              value_nature: "assumed",
            },
            viscosity: {
              value: viscosityVal,
              unit: "mPa*s",
              provenance: "user_assumption",
              value_nature: "assumed",
            },
            oxygen_saturation_concentration: {
              value: cStarVal,
              unit: "mmol/L",
              provenance: "user_assumption",
              value_nature: "assumed",
            },
          },
          process_parameters: selectedProject.latest_passport?.process_parameters || [],
          change_note: `Updated medium properties (${recipeVersion})`,
        }),
      });
      const updatedProj = await apiFetch<Project>(`/projects/${selectedProject.id}`);
      await selectProject(updatedProj);
      setStatusBanner(`Created immutable Process Passport version for ${updatedProj.name}`);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to save passport version");
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadAndImportBatch(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProject || !uploadFile) return;
    setBusy(true);
    setErrorBanner(null);
    try {
      const fd = new FormData();
      fd.append("file", uploadFile);
      fd.append("is_synthetic", "true");
      fd.append("source_description", "User uploaded fermentation batch export");

      const uploaded = await apiFetch<{ id: string }>(`/projects/${selectedProject.id}/files`, {
        method: "POST",
        body: fd,
      });

      const preview = await apiFetch<{
        columns: Array<{
          name: string;
          Suggested_variable: string | null;
          Suggested_unit: string | null;
        }>;
      }>(`/files/${uploaded.id}/preview`);

      const tsCol =
        preview.columns.find((c) => c.name.toLowerCase().includes("elapsed") || c.name.toLowerCase().includes("time"))
          ?.name || preview.columns[0].name;

      const mappedCols = preview.columns
        .filter((c) => c.name !== tsCol && c.Suggested_variable && c.Suggested_unit)
        .map((c) => ({
          source: c.name,
          variable: c.Suggested_variable,
          unit: c.Suggested_unit,
          provenance: "sensor",
          calibration_status: "calibrated_pre_run",
        }));

      await apiFetch(`/files/${uploaded.id}/mapping`, {
        method: "PUT",
        body: JSON.stringify({
          mapping: {
            sheet: "CSV",
            header_row: 1,
            timestamp: { column: tsCol, kind: "elapsed", elapsed_unit: "h" },
            batch_start: new Date().toISOString(),
            columns: mappedCols,
          },
        }),
      });

      const dryRun = await apiFetch<QualityReport>(`/files/${uploaded.id}/dry-run`, {
        method: "POST",
      });
      setLastQualityReport(dryRun);

      if (!dryRun.blocking) {
        await apiFetch(`/files/${uploaded.id}/import`, {
          method: "POST",
          body: JSON.stringify({
            run_code: uploadRunCode,
            scale_label: "2 L Lab",
            working_volume: uploadVolume,
            working_volume_unit: "L",
            vessel_version_id: vessels[0]?.latest_version.id || null,
            passport_version_id: selectedProject.latest_passport?.id || null,
            operator: user?.full_name || "Scientist",
          }),
        });
        await selectProject(selectedProject);
        setStatusBanner(`Batch '${uploadRunCode}' validated with Pint and imported.`);
      }
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Batch import failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleRunScaleUpScenario(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProject || vessels.length < 2) return;
    setBusy(true);
    setErrorBanner(null);
    try {
      const labV = vessels.find((v) => v.scale_class === "lab") || vessels[0];
      const pilotV = vessels.find((v) => v.scale_class === "pilot") || vessels[1];

      const createdScen = await apiFetch<{ id: string }>(
        `/projects/${selectedProject.id}/scenarios`,
        {
          method: "POST",
          body: JSON.stringify({
            name: scenName,
            batch_ids: batches.map((b) => b.id),
            source_vessel_version_id: labV.latest_version.id,
            target_vessel_version_id: pilotV.latest_version.id,
            target_working_volume: {
              value: targetVolL,
              unit: "L",
              provenance: "manual_entry",
            },
            criteria: [
              { criterion_id: "S-PV", is_primary: primaryCrit === "S-PV" },
              { criterion_id: "S-TIP", is_primary: primaryCrit === "S-TIP" },
              { criterion_id: "S-KLA", is_primary: false },
            ],
            aeration_basis: aerationBasis,
            kla_selection: {
              source_point_id: labV.latest_version.kla_evidence[0]?.id || null,
              target_point_id: pilotV.latest_version.kla_evidence[0]?.id || null,
            },
            constraints: [
              {
                key: "min_do_required",
                value: minDoReq,
                unit: "% air sat",
                provenance: "user_assumption",
              },
              {
                key: "max_tip_speed",
                value: maxTipConstraint,
                unit: "m/s",
                provenance: "user_assumption",
              },
            ],
            assumptions: [],
            thresholds: {},
          }),
        }
      );

      const newAssessment = await apiFetch<AssessmentRecord>(
        `/scenarios/${createdScen.id}/assessments`,
        { method: "POST" }
      );
      setAssessment(newAssessment);
      setActiveTab("readiness");
      setStatusBanner(
        `Executed deterministic scale-up assessment (${newAssessment.calculations.length} calculations, ${newAssessment.risk_flags.length} risk evaluations).`
      );
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to run assessment");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateTaskStatus(
    taskId: string,
    newStatus: "open" | "in_progress" | "done" | "waived"
  ) {
    if (!assessment) return;
    let waivedReason: string | null = null;
    if (newStatus === "waived") {
      waivedReason = window.prompt(
        "Enter mandatory engineering justification for waiving this validation task:"
      );
      if (!waivedReason || !waivedReason.trim()) return;
    }
    setBusy(true);
    try {
      await apiFetch(`/validation-tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus, waived_reason: waivedReason }),
      });
      const refreshed = await apiFetch<AssessmentRecord>(`/assessments/${assessment.id}`);
      setAssessment(refreshed);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Failed to update task");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!assessment) return;
    setBusy(true);
    setErrorBanner(null);
    try {
      await apiFetch(`/assessments/${assessment.id}/reviews`, {
        method: "POST",
        body: JSON.stringify({
          decision: reviewDecision,
          comment: reviewComment,
        }),
      });
      const refreshed = await apiFetch<AssessmentRecord>(`/assessments/${assessment.id}`);
      setAssessment(refreshed);
      setStatusBanner("Recorded domain-expert review sign-off on assessment.");
    } catch (err) {
      setErrorBanner(
        err instanceof Error
          ? `${err.message} (Switch to Reviewer account in header to sign off)`
          : "Review sign-off failed"
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleGeneratePdfReport() {
    if (!assessment) return;
    setBusy(true);
    setErrorBanner(null);
    try {
      const rep = await apiFetch<{ id: string; version: number }>(
        `/assessments/${assessment.id}/reports`,
        { method: "POST" }
      );
      const refreshed = await apiFetch<AssessmentRecord>(`/assessments/${assessment.id}`);
      setAssessment(refreshed);
      setStatusBanner(`Generated Process-Transfer Report PDF v${rep.version}`);

      // Trigger authenticated PDF download
      const { token, orgId } = getStoredAuth();
      const res = await fetch(getReportDownloadUrl(rep.id), {
        headers: {
          Authorization: `Bearer ${token || ""}`,
          "X-Organization-Id": orgId || "",
        },
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
      setErrorBanner(err instanceof Error ? err.message : "Report generation failed");
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-navy-900 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-xl shadow-xl border border-slate-200 p-8">
          <div className="flex items-center gap-2 text-xs font-bold tracking-widest uppercase text-teal-600">
            <span>Biomanufacturing / Deep Tech</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">ScaleBridge Bio</h1>
          <p className="text-xs text-slate-600 mt-1">
            Vendor-agnostic bioprocess scale-up readiness & technology-transfer decision support.
          </p>

          <form onSubmit={handleLogin} className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                required
              />
            </div>
            {authError && (
              <div className="p-2.5 rounded bg-red-50 border border-red-200 text-xs text-red-800">
                {authError}
              </div>
            )}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-md bg-teal-600 hover:bg-teal-500 text-white font-semibold py-2.5 text-sm transition"
            >
              {busy ? "Signing in..." : "Sign In to Engineering Workspace"}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-200 text-xs text-slate-500 space-y-1">
            <p className="font-semibold text-slate-700">Seeded Demo Accounts (Password: ScaleBridge2026!)</p>
            <p className="font-mono">• scientist@scalebridge.bio (Role: scientist)</p>
            <p className="font-mono">• reviewer@scalebridge.bio (Role: reviewer)</p>
            <p className="font-mono">• admin@scalebridge.bio (Role: org_admin)</p>
          </div>
        </div>
      </div>
    );
  }

  const activeRole = user.memberships[0]?.role || "scientist";

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Persistent Synthetic Data Banner (Blueprint p.5 requirement) */}
      {(selectedProject?.is_synthetic_demo || assessment?.is_synthetic) && (
        <div className="bg-amber-400 text-slate-950 px-6 py-1.5 text-xs font-semibold flex items-center justify-between">
          <span>
            SYNTHETIC / DEMONSTRATION DATASET ACTIVE — Clearly labeled synthetic data for workflow
            demonstration (Blueprint p.5). Do not use for physical bioreactor operation.
          </span>
          <span className="font-mono text-[11px] bg-amber-950 text-amber-100 px-2 py-0.5 rounded">
            is_synthetic_demo = true
          </span>
        </div>
      )}

      {/* Top Navigation Header */}
      <header className="bg-navy-900 text-white px-6 py-3.5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-lg">SCALEBRIDGE BIO</span>
              <span className="text-[11px] bg-teal-600/30 text-teal-300 border border-teal-500/40 px-2 py-0.5 rounded font-mono">
                Decision Support Workspace
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {user.memberships[0]?.name} · Active Project:{" "}
              <span className="text-slate-200 font-medium">{selectedProject?.name}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="bg-navy-800 border border-slate-700 rounded px-2.5 py-1 flex items-center gap-2">
            <span className="text-slate-400">Role Switcher:</span>
            <button
              onClick={() => void quickSwitchAccount("scientist@scalebridge.bio")}
              className={`px-2 py-0.5 rounded ${
                user.email.startsWith("scientist") ? "bg-teal-600 text-white font-semibold" : "text-slate-300 hover:text-white"
              }`}
            >
              Scientist
            </button>
            <button
              onClick={() => void quickSwitchAccount("reviewer@scalebridge.bio")}
              className={`px-2 py-0.5 rounded ${
                user.email.startsWith("reviewer") ? "bg-teal-600 text-white font-semibold" : "text-slate-300 hover:text-white"
              }`}
            >
              Advisor / Reviewer
            </button>
          </div>

          <span className="text-slate-300">
            {user.full_name} (<span className="font-mono text-teal-300">{activeRole}</span>)
          </span>
          <button
            onClick={() => {
              clearStoredAuth();
              setUser(null);
            }}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* 4-Stage Blueprint Bar (01 LAB DATA | 02 ENGINEERING | 03 RISK REVIEW | 04 TRANSFER) */}
      <div className="bg-white border-b border-slate-200 px-6 py-2.5">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "passport", stage: "01 / LAB DATA", label: "Process Passport & Checklist" },
              { id: "ingestion", stage: "01 / LAB DATA", label: "Batch Ingestion & Dashboard" },
              { id: "vessels", stage: "02 / ENGINEERING", label: "Vessel Profiles & Comparison" },
              { id: "scenarios", stage: "02 / ENGINEERING", label: "Scale-Up Scenario Builder" },
              { id: "readiness", stage: "03 / RISK REVIEW", label: "Calculations, Trade-Offs & Risks" },
              { id: "validation", stage: "04 / TRANSFER", label: "Validation Plan & PDF Report" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as StageTab)}
                className={`px-3.5 py-2 rounded-md text-xs font-semibold transition border ${
                  activeTab === tab.id
                    ? "bg-navy-900 text-white border-navy-900 shadow-sm"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                <span className="block text-[10px] font-mono text-teal-500">{tab.stage}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {!assessment && (
            <button
              onClick={(e) => void handleRunScaleUpScenario(e)}
              disabled={busy}
              className="px-4 py-2 rounded-md bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold shadow-sm transition"
            >
              {busy ? "Computing..." : "Run Default 2 L → 150 L Scale-Up Assessment →"}
            </button>
          )}
        </div>
      </div>

      {/* Status & Error Banners */}
      <div className="max-w-7xl w-full mx-auto px-6 pt-4 space-y-2">
        {statusBanner && (
          <div className="p-3 rounded-md bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-center justify-between">
            <span>{statusBanner}</span>
            <button onClick={() => setStatusBanner(null)} className="font-bold">
              ✕
            </button>
          </div>
        )}
        {errorBanner && (
          <div className="p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-900 flex items-center justify-between">
            <span>{errorBanner}</span>
            <button onClick={() => setErrorBanner(null)} className="font-bold">
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <main className="max-w-7xl w-full mx-auto px-6 py-6 flex-1 space-y-6">
        {/* TAB 1: PROCESS PASSPORT & DATA CHECKLIST */}
        {activeTab === "passport" && selectedProject && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                    Signature Module 1 · Versioned Process Record
                  </span>
                  <h2 className="text-lg font-bold text-slate-900">
                    Process Passport — {selectedProject.name}
                  </h2>
                </div>
                <span className="font-mono text-xs bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
                  Passport v{selectedProject.latest_passport?.version || 1} (
                  {selectedProject.latest_passport?.recipe_version})
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-slate-50 p-3.5 rounded-md border border-slate-200">
                <div>
                  <span className="text-slate-500 block">Organism / Strain</span>
                  <span className="font-semibold text-slate-900">
                    {selectedProject.organism_name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Product Family</span>
                  <span className="font-semibold text-slate-900">
                    {selectedProject.product_family}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Process Mode</span>
                  <span className="font-semibold text-slate-900 uppercase">
                    {selectedProject.process_type}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {selectedProject.latest_passport?.process_description}
              </p>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                  Documented Process Setpoints & Provenance
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {selectedProject.latest_passport?.process_parameters.map((pp) => (
                    <div
                      key={pp.key}
                      className="p-2.5 rounded border border-slate-200 bg-white text-xs"
                    >
                      <div className="font-mono text-[11px] text-slate-500">{pp.key}</div>
                      <div className="text-sm font-bold text-slate-900 mt-0.5">
                        {pp.value} {pp.unit}
                      </div>
                      <div className="flex items-center gap-1 mt-1.5">
                        <ProvenanceBadge provenance={pp.provenance} />
                        <NatureBadge nature={pp.value_nature} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <form
                onSubmit={handleSavePassportVersion}
                className="pt-4 border-t border-slate-200 space-y-3"
              >
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Medium Physical Context (Create New Immutable Passport Version)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Recipe Version
                    </label>
                    <input
                      type="text"
                      value={recipeVersion}
                      onChange={(e) => setRecipeVersion(e.target.value)}
                      className="w-full rounded border border-slate-300 px-2.5 py-1.5 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Density ρ (kg/m³)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={densityVal}
                      onChange={(e) => setDensityVal(Number(e.target.value))}
                      className="w-full rounded border border-slate-300 px-2.5 py-1.5 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Viscosity μ (mPa·s)
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      value={viscosityVal}
                      onChange={(e) => setViscosityVal(Number(e.target.value))}
                      className="w-full rounded border border-slate-300 px-2.5 py-1.5 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      O₂ Saturation C* (mmol/L)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={cStarVal}
                      onChange={(e) => setCStarVal(Number(e.target.value))}
                      className="w-full rounded border border-slate-300 px-2.5 py-1.5 font-mono"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-4 py-2 rounded bg-navy-900 hover:bg-navy-800 text-white text-xs font-semibold"
                >
                  Save New Immutable Passport Version
                </button>
              </form>
            </div>

            {/* Automated Data Checklist Panel */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
              <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                Readiness Prerequisite Check
              </span>
              <h3 className="text-base font-bold text-slate-900">Automated Data Checklist</h3>
              <p className="text-xs text-slate-600">
                Tracks which parameters required by downstream scale-up equations are measured,
                assumed, or missing.
              </p>

              <div className="space-y-2 pt-2">
                {checklist?.items.map((item) => (
                  <div
                    key={item.key}
                    className="p-2.5 rounded border border-slate-200 bg-slate-50 text-xs flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="font-semibold text-slate-800">{item.label}</div>
                      <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                        Required by: {item.required_by.join(", ")}
                      </div>
                    </div>
                    <NatureBadge
                      nature={
                        (item.status === "present"
                          ? "measured"
                          : item.status === "missing"
                          ? "insufficient"
                          : item.status) as never
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: BATCH INGESTION & PROCESS DASHBOARD */}
        {activeTab === "ingestion" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      Stage 01 · Laboratory Batch Records
                    </span>
                    <h2 className="text-base font-bold text-slate-900">
                      Imported Fermentation Batches ({batches.length})
                    </h2>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                        <th className="py-2 px-3">Run Code</th>
                        <th className="py-2 px-3">Scale / Working Vol</th>
                        <th className="py-2 px-3">Median RPM</th>
                        <th className="py-2 px-3">Median Airflow</th>
                        <th className="py-2 px-3">Min DO (% air sat)</th>
                        <th className="py-2 px-3">Peak OUR</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {batches.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-mono font-semibold text-slate-900">
                            {b.run_code}
                          </td>
                          <td className="py-2.5 px-3">
                            {b.scale_label} ({b.working_volume_original} {b.working_volume_unit})
                          </td>
                          <td className="py-2.5 px-3 font-mono">
                            {b.summary.agitation_speed?.median_display?.toFixed(0) || "—"} rpm
                          </td>
                          <td className="py-2.5 px-3 font-mono">
                            {b.summary.airflow?.median_display?.toFixed(2) || "—"} L/min
                          </td>
                          <td className="py-2.5 px-3 font-mono font-semibold text-amber-800">
                            {b.summary.dissolved_oxygen?.min_display?.toFixed(1) || "—"} %
                          </td>
                          <td className="py-2.5 px-3 font-mono">
                            {b.summary.our?.max_display?.toFixed(1) || "—"} mmol/(L·h)
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* CSV/XLSX Upload & Pint Unit Normalization Form */}
              <form
                onSubmit={handleUploadAndImportBatch}
                className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3"
              >
                <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                  Ingestion Pipeline · Pint + DQ Checks
                </span>
                <h3 className="text-base font-bold text-slate-900">Import CSV / XLSX Batch</h3>
                <div className="text-xs space-y-2.5">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Select CSV or XLSX Export
                    </label>
                    <input
                      type="file"
                      accept=".csv,.xlsx"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      className="w-full text-xs"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">Run Code</label>
                      <input
                        type="text"
                        value={uploadRunCode}
                        onChange={(e) => setUploadRunCode(e.target.value)}
                        className="w-full rounded border border-slate-300 px-2 py-1 font-mono"
                        required
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Working Vol (L)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={uploadVolume}
                        onChange={(e) => setUploadVolume(Number(e.target.value))}
                        className="w-full rounded border border-slate-300 px-2 py-1 font-mono"
                        required
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={busy || !uploadFile}
                    className="w-full py-2 rounded bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs"
                  >
                    Upload, Validate Units & Import Batch
                  </button>
                </div>

                {lastQualityReport && (
                  <div className="mt-3 p-2.5 rounded bg-slate-50 border border-slate-200 text-xs">
                    <p className="font-semibold text-slate-800">
                      Data-Quality Summary: {lastQualityReport.rows_imported}/
                      {lastQualityReport.rows_total} rows valid
                    </p>
                    <p className="text-[11px] text-slate-600 mt-0.5">
                      Conversions logged: {lastQualityReport.conversions.length} · Issues:{" "}
                      {lastQualityReport.issues.length}
                    </p>
                  </div>
                )}
              </form>
            </div>

            {/* Multi-Batch Overlay Process Dashboard (Blueprint p.5 Acceptance Test) */}
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                    Multi-Batch Overlay · Elapsed Time Alignment
                  </span>
                  <h3 className="text-base font-bold text-slate-900">
                    Fermentation Process Trends (pH, DO, Temp, RPM, Airflow, OUR, Biomass, Titre)
                  </h3>
                </div>
                <span className="text-xs text-slate-500">
                  Gaps are never interpolated · Invalid readings excluded
                </span>
              </div>

              <BatchTrendChart
                batches={overlaySeries}
                selectedVariables={[
                  "dissolved_oxygen",
                  "agitation_speed",
                  "our",
                  "biomass_dcw",
                  "product_titre",
                  "ph",
                  "temperature",
                  "airflow",
                ]}
              />
            </div>
          </div>
        )}

        {/* TAB 3: VESSEL PROFILES & COMPARISON */}
        {activeTab === "vessels" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {vessels.map((v) => (
                <div
                  key={v.id}
                  className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                        {v.scale_class.toUpperCase()} VESSEL · Version v{v.latest_version.version}
                      </span>
                      <h3 className="text-base font-bold text-slate-900">{v.name}</h3>
                      <p className="text-xs text-slate-500">
                        {v.manufacturer} {v.model} · {v.location}
                      </p>
                    </div>
                    <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded border border-slate-200">
                      {v.latest_version.impeller_type} (n={v.latest_version.impeller_count})
                    </span>
                  </div>

                  {v.missing_specifications.length > 0 && (
                    <div className="p-3 rounded bg-amber-50 border border-amber-300 text-xs text-amber-950">
                      <p className="font-semibold">
                        Missing-Specification Warning ({v.missing_specifications.length} parameter
                        gap)
                      </p>
                      <ul className="mt-1 space-y-0.5 font-mono text-[11px]">
                        {v.missing_specifications.map((ms) => (
                          <li key={ms.key}>
                            • {ms.key} (required by{" "}
                            {[...ms.required_by_formulas, ...ms.required_by_checks].join(", ")})
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(v.latest_version.parameters).map(([pkey, q]) => (
                      <div
                        key={pkey}
                        className="p-2 rounded bg-slate-50 border border-slate-200 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-mono text-[11px] text-slate-500">{pkey}</div>
                          <div className="font-semibold text-slate-900">
                            {formatQuantity(q, 4)}
                          </div>
                        </div>
                        <ProvenanceBadge provenance={q.provenance} />
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-slate-200 text-xs space-y-1">
                    <div className="font-semibold text-slate-700">
                      Documented kLa Evidence Points ({v.latest_version.kla_evidence.length}):
                    </div>
                    {v.latest_version.kla_evidence.map((kp) => (
                      <div
                        key={kp.id}
                        className="p-2 rounded bg-teal-50/50 border border-teal-200 text-xs"
                      >
                        <span className="font-mono font-bold text-teal-900">
                          {kp.id}: kLa = {formatQuantity(kp.kla)}
                        </span>{" "}
                        · Medium: {kp.medium_description} ({kp.method})
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {vesselComparison && (
              <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
                <h3 className="text-sm font-bold text-slate-900">
                  Geometric Similarity Ratios (F-GEO-001 & F-GEO-002)
                </h3>
                <p className="text-xs text-slate-600 mt-1">
                  Source Lab Vessel D/T ={" "}
                  <span className="font-mono font-semibold">
                    {Number(
                      (
                        (vesselComparison.geometric_ratios as Record<string, Record<string, number>>)
                          ?.vessel_a?.D_over_T || 0
                      ).toFixed(3)
                    )}
                  </span>{" "}
                  vs Target Pilot Vessel D/T ={" "}
                  <span className="font-mono font-semibold">
                    {Number(
                      (
                        (vesselComparison.geometric_ratios as Record<string, Record<string, number>>)
                          ?.vessel_b?.D_over_T || 0
                      ).toFixed(3)
                    )}
                  </span>
                </p>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: SCALE-UP SCENARIO BUILDER */}
        {activeTab === "scenarios" && (
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm max-w-3xl">
            <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
              Stage 02 · Engineering Scenario Configuration
            </span>
            <h2 className="text-lg font-bold text-slate-900 mt-1">
              Configure Scale-Up Scenario & Execute Deterministic Engine
            </h2>
            <p className="text-xs text-slate-600 mt-1">
              No single scale-up criterion is universally appropriate: preserving constant P/V
              changes tip speed and Reynolds number, and vice versa (Blueprint p.6).
            </p>

            <form onSubmit={handleRunScaleUpScenario} className="mt-5 space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Scenario Name</label>
                <input
                  type="text"
                  value={scenName}
                  onChange={(e) => setScenName(e.target.value)}
                  className="w-full rounded border border-slate-300 px-3 py-2"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Target Working Volume (L)
                  </label>
                  <input
                    type="number"
                    step="1"
                    value={targetVolL}
                    onChange={(e) => setTargetVolL(Number(e.target.value))}
                    className="w-full rounded border border-slate-300 px-3 py-2 font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Primary Agitation Criterion
                  </label>
                  <select
                    value={primaryCrit}
                    onChange={(e) => setPrimaryCrit(e.target.value as "S-PV" | "S-TIP")}
                    className="w-full rounded border border-slate-300 px-3 py-2"
                  >
                    <option value="S-PV">S-PV (Constant Power/Volume P/V)</option>
                    <option value="S-TIP">S-TIP (Constant Tip Speed u_tip)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Aeration Basis</label>
                  <select
                    value={aerationBasis}
                    onChange={(e) => setAerationBasis(e.target.value as "S-VVM" | "S-VS")}
                    className="w-full rounded border border-slate-300 px-3 py-2"
                  >
                    <option value="S-VVM">S-VVM (Constant vvm)</option>
                    <option value="S-VS">S-VS (Constant Superficial Velocity v_s)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Constraint: Minimum Required DO (% air sat)
                  </label>
                  <input
                    type="number"
                    step="1"
                    value={minDoReq}
                    onChange={(e) => setMinDoReq(Number(e.target.value))}
                    className="w-full rounded border border-slate-300 px-3 py-2 font-mono"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Constraint: Max Allowable Tip Speed (m/s)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={maxTipConstraint}
                    onChange={(e) => setMaxTipConstraint(Number(e.target.value))}
                    className="w-full rounded border border-slate-300 px-3 py-2 font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={busy}
                className="px-5 py-2.5 rounded-md bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow-sm"
              >
                {busy ? "Running Assessment..." : "Execute Scale-Up Assessment & Risk Engine"}
              </button>
            </form>
          </div>
        )}

        {/* TAB 5: READINESS REVIEW (CALCULATIONS, TRADE-OFFS, COMPATIBILITY, RISK REGISTER) */}
        {activeTab === "readiness" && (
          <div className="space-y-6">
            {!assessment ? (
              <div className="bg-white rounded-lg border border-slate-200 p-8 text-center space-y-3">
                <p className="text-sm font-semibold text-slate-800">
                  No scale-up assessment has been executed in this session yet.
                </p>
                <button
                  onClick={(e) => void handleRunScaleUpScenario(e)}
                  className="px-4 py-2 rounded bg-teal-600 text-white text-xs font-bold"
                >
                  Run 2 L → 150 L Scale-Up Assessment Now
                </button>
              </div>
            ) : (
              <>
                {/* Summary Bar */}
                <div className="bg-navy-900 text-white rounded-lg p-5 grid grid-cols-2 sm:grid-cols-6 gap-4">
                  <div>
                    <div className="text-[11px] text-slate-400 uppercase">Overall Evidence</div>
                    <div className="mt-1">
                      <NatureBadge nature={assessment.summary.overall_evidence_level} />
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400 uppercase">Critical / High Risks</div>
                    <div className="text-xl font-bold text-orange-400 font-mono">
                      {assessment.summary.triggered_by_severity.critical || 0} /{" "}
                      {assessment.summary.triggered_by_severity.high || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400 uppercase">Medium Risks</div>
                    <div className="text-xl font-bold text-amber-300 font-mono">
                      {assessment.summary.triggered_by_severity.medium || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400 uppercase">
                      Insufficient Evidence
                    </div>
                    <div className="text-xl font-bold text-amber-200 font-mono">
                      {assessment.summary.insufficient_evidence_flag_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400 uppercase">Validation Tasks</div>
                    <div className="text-xl font-bold text-teal-300 font-mono">
                      {assessment.summary.validation_task_count}
                    </div>
                  </div>
                  <div className="flex items-center justify-end">
                    <button
                      onClick={() => setActiveTab("validation")}
                      className="px-3 py-2 rounded bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold"
                    >
                      View Validation Plan & PDF →
                    </button>
                  </div>
                </div>

                {/* Criterion Trade-Off Matrix */}
                <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
                  <div>
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      Scale-Up Criterion Trade-Offs (Blueprint p.4, p.6)
                    </span>
                    <h3 className="text-base font-bold text-slate-900">
                      Side-by-Side Criterion Comparison & Target Operating Point
                    </h3>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                          <th className="py-2 px-3">Criterion</th>
                          <th className="py-2 px-3">Target N (rpm)</th>
                          <th className="py-2 px-3">Target Q_g (L/min)</th>
                          <th className="py-2 px-3">Target P/V (ratio vs Lab)</th>
                          <th className="py-2 px-3">Target u_tip (ratio vs Lab)</th>
                          <th className="py-2 px-3">Target Re (ratio vs Lab)</th>
                          <th className="py-2 px-3">Target v_s (ratio vs Lab)</th>
                          <th className="py-2 px-3">Target OTR at DO_req</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {assessment.trade_offs.map((row) => (
                          <tr key={row.criterion_id} className="hover:bg-slate-50">
                            <td className="py-2.5 px-3 font-semibold text-slate-900">
                              <span className="font-mono text-teal-700">{row.criterion_id}</span>{" "}
                              {row.is_primary && (
                                <span className="ml-1 text-[10px] bg-navy-900 text-white px-1.5 py-0.5 rounded">
                                  PRIMARY
                                </span>
                              )}
                              <div className="text-[11px] text-slate-500 font-normal">
                                {row.criterion_name}
                              </div>
                            </td>
                            <td className="py-2.5 px-3 font-mono font-bold">
                              {formatQuantity(row.target_operating_point.N, 3)}
                            </td>
                            <td className="py-2.5 px-3 font-mono">
                              {formatQuantity(row.target_operating_point.Q_g, 3)}
                            </td>
                            <td className="py-2.5 px-3 font-mono">
                              {formatQuantity(row.descriptors_target.P_per_V, 3)}
                              {row.descriptor_ratios.P_per_V !== null && (
                                <span className="block text-[11px] text-slate-500">
                                  ({row.descriptor_ratios.P_per_V?.toFixed(2)}× Lab)
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 font-mono">
                              {formatQuantity(row.descriptors_target.u_tip, 3)}
                              {row.descriptor_ratios.u_tip !== null && (
                                <span className="block text-[11px] text-slate-500">
                                  ({row.descriptor_ratios.u_tip?.toFixed(2)}× Lab)
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 font-mono">
                              {formatQuantity(row.descriptors_target.Re, 3)}
                              {row.descriptor_ratios.Re !== null && (
                                <span className="block text-[11px] text-slate-500">
                                  ({row.descriptor_ratios.Re?.toFixed(2)}× Lab)
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 font-mono">
                              {formatQuantity(row.descriptors_target.v_s, 3)}
                              {row.descriptor_ratios.v_s !== null && (
                                <span className="block text-[11px] text-slate-500">
                                  ({row.descriptor_ratios.v_s?.toFixed(2)}× Lab)
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 font-mono">
                              {formatQuantity(row.descriptors_target.OTR, 3)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Explainable Risk Register */}
                <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
                  <div>
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      Signature Module 2 · Explainable Scale-Up Risk Register
                    </span>
                    <h3 className="text-base font-bold text-slate-900">
                      Rule-Based Engineering Warnings, Missing Evidence & Input Links
                    </h3>
                  </div>

                  <div className="space-y-3">
                    {assessment.risk_flags.map((rf) => (
                      <div
                        key={rf.id}
                        className={`p-4 rounded-lg border text-xs ${
                          rf.outcome === "triggered"
                            ? "bg-white border-slate-300 shadow-sm"
                            : rf.outcome === "insufficient_evidence"
                            ? "bg-amber-50/40 border-amber-300"
                            : "bg-slate-50 border-slate-200"
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                              {rf.rule_id} v{rf.rule_version}
                            </span>
                            <span className="uppercase font-semibold text-slate-500">
                              {rf.category.replace(/_/g, " ")}
                            </span>
                            <span className="font-bold text-slate-900 text-sm">{rf.title}</span>
                          </div>
                          <SeverityBadge severity={rf.severity} outcome={rf.outcome} />
                        </div>

                        <p className="mt-2 text-slate-700 leading-relaxed">{rf.explanation}</p>

                        {rf.evidence_gap && (
                          <div className="mt-2 p-2 rounded bg-amber-50 border border-amber-200 text-amber-950">
                            <span className="font-semibold">Evidence Gap to Resolve: </span>
                            {rf.evidence_gap}
                          </div>
                        )}

                        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500">
                          <span className="font-semibold">Linked Inputs:</span>
                          {rf.input_refs.map((iref, idx) => (
                            <span
                              key={idx}
                              className="font-mono bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200"
                            >
                              {iref.kind}:{iref.key}
                            </span>
                          ))}
                          {rf.validation_task_codes.length > 0 && (
                            <>
                              <span className="ml-2 font-semibold">Validation Tasks:</span>
                              {rf.validation_task_codes.map((vc) => (
                                <span
                                  key={vc}
                                  className="font-mono bg-teal-50 text-teal-800 px-1.5 py-0.5 rounded border border-teal-200"
                                >
                                  {vc}
                                </span>
                              ))}
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Equipment Compatibility Envelope Table */}
                <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
                  <div>
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      Signature Module 3 · Equipment Compatibility Engine
                    </span>
                    <h3 className="text-base font-bold text-slate-900">
                      Target Vessel Capability Envelope Verification
                    </h3>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                          <th className="py-2 px-3">Check ID</th>
                          <th className="py-2 px-3">Criterion</th>
                          <th className="py-2 px-3">Requirement vs Envelope</th>
                          <th className="py-2 px-3">Outcome</th>
                          <th className="py-2 px-3">Engineering Explanation</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {assessment.compatibility_checks.map((chk) => (
                          <tr key={chk.id}>
                            <td className="py-2.5 px-3 font-mono font-semibold">{chk.check_id}</td>
                            <td className="py-2.5 px-3 font-mono">{chk.criterion_id || "All"}</td>
                            <td className="py-2.5 px-3">{chk.title}</td>
                            <td className="py-2.5 px-3">
                              <CompatBadge outcome={chk.outcome} />
                            </td>
                            <td className="py-2.5 px-3 text-slate-700">{chk.explanation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Full Calculation Cards with Equations, Units, Inputs & Assumptions */}
                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      100% Traceability · Deterministic Formula Cards
                    </span>
                    <h3 className="text-base font-bold text-slate-900">
                      Complete Engineering Calculation Audit Trail ({assessment.calculations.length}{" "}
                      evaluations)
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {assessment.calculations.map((calc) => (
                      <CalculationTraceCard key={calc.id} calc={calc} />
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* TAB 6: VALIDATION PLANNER, EXPERT SIGN-OFF & PDF TRANSFER REPORT */}
        {activeTab === "validation" && (
          <div className="space-y-6">
            {!assessment ? (
              <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
                <p className="text-sm font-semibold text-slate-700">
                  Run a Scale-Up Assessment first to generate the Validation Plan and Transfer Report.
                </p>
              </div>
            ) : (
              <>
                <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      Stage 04 · Technology-Transfer Package
                    </span>
                    <h2 className="text-lg font-bold text-slate-900">
                      Process-Transfer Passport & Prioritized Validation Plan
                    </h2>
                    <p className="text-xs text-slate-600">
                      Exports a versioned, SHA-256 hashed PDF report with process summary, vessel
                      comparison, traceable equations, risk register, and validation plan.
                    </p>
                  </div>
                  <button
                    onClick={() => void handleGeneratePdfReport()}
                    disabled={busy}
                    className="px-5 py-2.5 rounded-md bg-navy-900 hover:bg-navy-800 text-white text-xs font-bold shadow-sm"
                  >
                    {busy ? "Generating PDF..." : "Generate & Download PDF Transfer Report"}
                  </button>
                </div>

                {/* Prioritized Validation Tasks */}
                <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
                  <h3 className="text-base font-bold text-slate-900">
                    Signature Module 4 · Validation Planner ({assessment.validation_tasks.length}{" "}
                    Tasks)
                  </h3>
                  <div className="space-y-2.5">
                    {assessment.validation_tasks.map((vt) => (
                      <div
                        key={vt.id}
                        className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 flex flex-wrap items-start justify-between gap-3 text-xs"
                      >
                        <div className="space-y-1 max-w-3xl">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded font-mono font-bold ${
                                vt.priority === "P1"
                                  ? "bg-red-100 text-red-900 border border-red-300"
                                  : "bg-amber-100 text-amber-900 border border-amber-300"
                              }`}
                            >
                              {vt.priority}
                            </span>
                            <span className="font-mono font-semibold text-slate-700">
                              {vt.task_code}
                            </span>
                            <span className="uppercase text-[11px] bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-600">
                              {vt.task_type.replace(/_/g, " ")}
                            </span>
                            <span className="font-bold text-slate-900 text-sm">{vt.title}</span>
                          </div>
                          <p className="text-slate-600">{vt.description}</p>
                          {vt.waived_reason && (
                            <p className="text-amber-900 font-semibold">
                              Waived Reason: {vt.waived_reason}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center gap-1.5">
                          {(["open", "in_progress", "done", "waived"] as const).map((st) => (
                            <button
                              key={st}
                              onClick={() => void handleUpdateTaskStatus(vt.id, st)}
                              className={`px-2.5 py-1 rounded text-[11px] font-semibold border ${
                                vt.status === st
                                  ? "bg-teal-600 text-white border-teal-600"
                                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
                              }`}
                            >
                              {st.replace(/_/g, " ")}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Human Reviewer Sign-Off Panel */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <form
                    onSubmit={handleSubmitReview}
                    className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3 text-xs"
                  >
                    <span className="text-xs font-mono uppercase text-teal-600 font-semibold">
                      Safeguard · Human Engineering Sign-Off (Blueprint p.15)
                    </span>
                    <h3 className="text-base font-bold text-slate-900">
                      Record Bioprocess Reviewer Decision
                    </h3>
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">Decision</label>
                      <select
                        value={reviewDecision}
                        onChange={(e) =>
                          setReviewDecision(
                            e.target.value as "approved_for_discussion" | "changes_requested"
                          )
                        }
                        className="w-full rounded border border-slate-300 px-3 py-2"
                      >
                        <option value="approved_for_discussion">
                          Approved for Pilot Facility Discussion
                        </option>
                        <option value="changes_requested">
                          Changes / Additional Measurements Requested
                        </option>
                      </select>
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Engineering Review Notes
                      </label>
                      <textarea
                        rows={3}
                        value={reviewComment}
                        onChange={(e) => setReviewComment(e.target.value)}
                        className="w-full rounded border border-slate-300 px-3 py-2"
                        required
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={busy}
                      className="px-4 py-2 rounded bg-teal-600 hover:bg-teal-500 text-white font-semibold"
                    >
                      Record Sign-Off (Requires Reviewer or Org Admin Role)
                    </button>
                  </form>

                  <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3 text-xs">
                    <h3 className="text-base font-bold text-slate-900">
                      Recorded Reviews & Generated PDF Reports
                    </h3>
                    <div className="space-y-2">
                      {assessment.reviews.length === 0 ? (
                        <p className="text-slate-500">No expert reviews recorded yet.</p>
                      ) : (
                        assessment.reviews.map((rev) => (
                          <div
                            key={rev.id}
                            className="p-3 rounded bg-emerald-50 border border-emerald-200"
                          >
                            <div className="font-bold text-emerald-950">
                              {rev.reviewer_name} — {rev.decision.replace(/_/g, " ").toUpperCase()}
                            </div>
                            <p className="text-emerald-900 mt-1">{rev.comment}</p>
                          </div>
                        ))
                      )}
                    </div>

                    <div className="pt-3 border-t border-slate-200 space-y-1.5">
                      <div className="font-semibold text-slate-700">
                        Generated PDF Transfer Reports ({assessment.reports.length}):
                      </div>
                      {assessment.reports.map((rep) => (
                        <div
                          key={rep.id}
                          className="p-2 rounded bg-slate-50 border border-slate-200 flex items-center justify-between font-mono text-[11px]"
                        >
                          <span>
                            v{rep.version} · {(rep.size_bytes / 1024).toFixed(1)} KB · SHA256:{" "}
                            {rep.sha256.slice(0, 12)}…
                          </span>
                          <span className="text-teal-700 font-semibold">Saved</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
