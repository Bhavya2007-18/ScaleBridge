import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { setToken } from '../lib/auth';

interface LoginProps {
  onSuccess: () => void;
}

const SEEDED_ACCOUNTS = [
  { email: 'scientist@scalebridge.bio', role: 'scientist' },
  { email: 'reviewer@scalebridge.bio', role: 'reviewer' },
  { email: 'admin@scalebridge.bio', role: 'org_admin' },
];

export const Login: React.FC<LoginProps> = ({ onSuccess }) => {
  const [email, setEmail] = useState('scientist@scalebridge.bio');
  const [password, setPassword] = useState('ScaleBridge2026!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setToken(res.access_token);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  };

  const handleSkipDemo = () => {
    setToken('mock_demo_token');
    onSuccess();
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center items-center p-4 selection:bg-teal-500/20">
      {/* Centered Login Card */}
      <div className="max-w-[440px] w-full bg-white rounded-2xl shadow-xl border border-slate-200/80 p-8 sm:p-10">
        {/* Header Tag */}
        <div className="text-[11px] font-bold font-mono text-teal-600 tracking-wider uppercase mb-2">
          BIOMANUFACTURING / DEEP TECH
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-3xl font-display font-extrabold text-slate-900 tracking-tight">
          ScaleBridge Bio
        </h1>

        {/* Subtitle */}
        <p className="text-xs sm:text-sm text-slate-600 mt-2 leading-relaxed">
          Vendor-agnostic bioprocess scale-up readiness &amp; technology-transfer decision support.
        </p>

        {/* Error Notice */}
        {error && (
          <div className="mt-5 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-medium space-y-2">
            <div>{error}</div>
            <button
              type="button"
              onClick={handleSkipDemo}
              className="text-[11px] font-semibold text-teal-700 hover:text-teal-900 underline block"
            >
              Backend offline? Click here to continue in Demo Mode →
            </button>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-teal-600 focus:ring-1 focus:ring-teal-600 transition"
              placeholder="scientist@scalebridge.bio"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-teal-600 focus:ring-1 focus:ring-teal-600 transition"
              placeholder="••••••••••••••••"
            />
          </div>

          <div className="space-y-2.5 pt-2">
            {/* Primary Sign In Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm transition shadow-sm flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? 'Authenticating...' : 'Sign In to Engineering Workspace'}
            </button>

            {/* Skip / Demo Mode Button */}
            <button
              type="button"
              onClick={handleSkipDemo}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-700 font-medium text-xs tracking-wide transition flex items-center justify-center gap-1.5"
            >
              <span>Skip (Use Demo Mode)</span>
              <span>→</span>
            </button>
          </div>
        </form>

        {/* Divider */}
        <div className="mt-7 pt-5 border-t border-slate-100 text-xs text-slate-500">
          <div className="font-semibold text-slate-700 mb-2">
            Seeded Demo Accounts <span className="font-normal text-slate-500">(Password: ScaleBridge2026!)</span>
          </div>
          <ul className="space-y-1.5 text-[11px] font-mono">
            {SEEDED_ACCOUNTS.map((acc) => (
              <li
                key={acc.email}
                onClick={() => {
                  setEmail(acc.email);
                  setPassword('ScaleBridge2026!');
                }}
                className="cursor-pointer hover:text-teal-700 transition flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                <span className="underline decoration-slate-300 hover:decoration-teal-600">{acc.email}</span>
                <span className="text-slate-400">(Role: {acc.role})</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
