"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, setStoredAuth, UserProfile } from "@/lib/api";

const SEEDED_ACCOUNTS = [
  { email: "scientist@scalebridge.bio", role: "scientist" },
  { email: "reviewer@scalebridge.bio", role: "reviewer" },
  { email: "admin@scalebridge.bio", role: "org_admin" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("scientist@scalebridge.bio");
  const [password, setPassword] = useState("ScaleBridge2026!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSkipDemo = () => {
    const demoUser: UserProfile = {
      id: "usr_mock_demo_01",
      email: email || "scientist@scalebridge.bio",
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
    setStoredAuth("mock_demo_token", "org_mock_demo_01", demoUser);
    router.push("/dashboard");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const resp = await apiFetch<{ access_token: string; user: UserProfile }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const orgId = resp.user.memberships[0]?.organization_id || "";
      setStoredAuth(resp.access_token, orgId, resp.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to fetch");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#040812] text-slate-100 flex flex-col justify-center items-center p-4 selection:bg-cyan-500/20 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Login Card */}
      <div className="max-w-[440px] w-full bg-[#080D18]/90 backdrop-blur-xl rounded-2xl border border-slate-800 shadow-2xl p-8 sm:p-10 relative z-10">
        {/* Header Tag */}
        <div className="text-[11px] font-bold font-mono text-cyan-400 tracking-wider uppercase mb-2">
          BIOMANUFACTURING / DEEP TECH
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-3xl font-display font-extrabold text-white tracking-tight">
          ScaleBridge Bio
        </h1>

        {/* Subtitle */}
        <p className="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed">
          Vendor-agnostic bioprocess scale-up readiness &amp; technology-transfer decision support.
        </p>

        {/* Error Notice */}
        {error && (
          <div className="mt-5 p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-mono space-y-2">
            <div>{error}</div>
            <button
              type="button"
              onClick={handleSkipDemo}
              className="text-[11px] font-semibold text-cyan-300 hover:text-cyan-200 underline block"
            >
              Backend offline? Click here to continue in Demo Mode →
            </button>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#03060C] border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition font-mono"
              placeholder="scientist@scalebridge.bio"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#03060C] border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition font-mono"
              placeholder="••••••••••••••••"
            />
          </div>

          <div className="space-y-2.5 pt-2">
            {/* Primary Sign In Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-[#03060C] font-semibold text-xs tracking-wider uppercase font-mono transition shadow-lg shadow-cyan-400/20 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? "Authenticating..." : "Sign In to Engineering Workspace"}
            </button>

            {/* Skip / Demo Mode Button */}
            <button
              type="button"
              onClick={handleSkipDemo}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white font-mono text-xs tracking-wide uppercase transition flex items-center justify-center gap-1.5"
            >
              <span>Skip (Use Demo Mode)</span>
              <span>→</span>
            </button>
          </div>
        </form>

        {/* Divider */}
        <div className="mt-7 pt-5 border-t border-slate-800/80 text-xs text-slate-400">
          <div className="font-semibold text-slate-300 mb-2">
            Seeded Demo Accounts <span className="font-normal text-slate-500 font-mono">(Password: ScaleBridge2026!)</span>
          </div>
          <ul className="space-y-1.5 text-[11px] font-mono">
            {SEEDED_ACCOUNTS.map((acc) => (
              <li
                key={acc.email}
                onClick={() => {
                  setEmail(acc.email);
                  setPassword("ScaleBridge2026!");
                }}
                className="cursor-pointer hover:text-cyan-300 transition flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                <span className="underline decoration-slate-600 hover:decoration-cyan-400">{acc.email}</span>
                <span className="text-slate-500">(Role: {acc.role})</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Back to Home Link */}
      <div className="mt-6 text-center z-10">
        <Link href="/" className="text-xs font-mono text-slate-500 hover:text-slate-300 transition">
          ← Back to ScaleBridge 3D Showcase
        </Link>
      </div>
    </div>
  );
}
