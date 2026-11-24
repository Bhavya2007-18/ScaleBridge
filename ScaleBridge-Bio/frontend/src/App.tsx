import React, { useState } from 'react';
import { DemoDataBanner } from './components/DemoDataBanner';
import { Login } from './routes/Login';
import { Projects } from './routes/Projects';
import { ProcessPassport } from './routes/ProcessPassport';
import { BatchImport } from './routes/BatchImport';
import { Vessels } from './routes/Vessels';
import { ScenarioBuilder } from './routes/ScenarioBuilder';
import { AssessmentResults } from './routes/AssessmentResults';
import { Report } from './routes/Report';
import { Project, Assessment } from './api/types';
import { isAuthenticated, clearToken } from './lib/auth';

type View =
  | 'login'
  | 'projects'
  | 'passport'
  | 'batch_import'
  | 'vessels'
  | 'scenario'
  | 'assessment'
  | 'report';

export default function App() {
  const [currentView, setCurrentView] = useState<View>(isAuthenticated() ? 'projects' : 'login');
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [latestAssessment, setLatestAssessment] = useState<Assessment | null>(null);

  const handleLogout = () => {
    clearToken();
    setCurrentView('login');
  };

  if (currentView === 'login') {
    return <Login onSuccess={() => setCurrentView('projects')} />;
  }

  return (
    <div className="min-h-screen euronium-bg-mesh text-[#e3e9e5] font-sans flex flex-col selection:bg-[#2fe578]/20 selection:text-[#2fe578] relative overflow-x-hidden">
      {/* Background ambient light gradients */}
      <div className="fixed top-0 left-1/4 w-[500px] h-[500px] bg-[#2fe578]/5 rounded-full blur-[140px] pointer-events-none -z-10"></div>
      <div className="fixed bottom-0 right-1/4 w-[600px] h-[600px] bg-[#143d25]/10 rounded-full blur-[160px] pointer-events-none -z-10"></div>

      {/* Top Banner */}
      <DemoDataBanner />

      {/* Euronium Floating Glass Navigation Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#080c09]/80 border-b border-white/5 px-6 lg:px-12 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => setCurrentView('projects')}
            >
              <div className="w-9 h-9 rounded-full bg-[#2fe578]/10 border border-[#2fe578]/40 flex items-center justify-center text-[#2fe578] font-mono text-xs font-bold group-hover:scale-105 transition">
                SB
              </div>
              <div>
                <span className="font-display font-bold tracking-tight text-base text-white block">
                  ScaleBridge Bio
                </span>
                <span className="text-[10px] font-mono text-[#708076] tracking-widest uppercase block -mt-1">
                  NATURE SCALE LEDGER
                </span>
              </div>
            </div>

            {/* Editorial Nav Tabs */}
            <nav className="hidden md:flex items-center gap-1 text-xs font-mono">
              <button
                onClick={() => setCurrentView('projects')}
                className={`px-3.5 py-1.5 rounded-full transition ${
                  currentView === 'projects'
                    ? 'bg-[#2fe578]/15 text-[#2fe578] border border-[#2fe578]/30'
                    : 'text-[#8e9e94] hover:text-white hover:bg-white/5'
                }`}
              >
                PASS-INDEX
              </button>
              {selectedProject && (
                <button
                  onClick={() => setCurrentView('passport')}
                  className={`px-3.5 py-1.5 rounded-full transition ${
                    currentView === 'passport'
                      ? 'bg-[#2fe578]/15 text-[#2fe578] border border-[#2fe578]/30'
                      : 'text-[#8e9e94] hover:text-white hover:bg-white/5'
                  }`}
                >
                  PASSPORT
                </button>
              )}
              <button
                onClick={() => setCurrentView('vessels')}
                className={`px-3.5 py-1.5 rounded-full transition ${
                  currentView === 'vessels'
                    ? 'bg-[#2fe578]/15 text-[#2fe578] border border-[#2fe578]/30'
                    : 'text-[#8e9e94] hover:text-white hover:bg-white/5'
                }`}
              >
                VESSELS
              </button>
              <button
                onClick={() => setCurrentView('batch_import')}
                className={`px-3.5 py-1.5 rounded-full transition ${
                  currentView === 'batch_import'
                    ? 'bg-[#2fe578]/15 text-[#2fe578] border border-[#2fe578]/30'
                    : 'text-[#8e9e94] hover:text-white hover:bg-white/5'
                }`}
              >
                DATA INGEST
              </button>
              <button
                onClick={() => setCurrentView('scenario')}
                className={`px-3.5 py-1.5 rounded-full transition ${
                  currentView === 'scenario'
                    ? 'bg-[#2fe578]/15 text-[#2fe578] border border-[#2fe578]/30'
                    : 'text-[#8e9e94] hover:text-white hover:bg-white/5'
                }`}
              >
                MODELER
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[#8e9e94]">
              <span className="w-2 h-2 rounded-full bg-[#2fe578]"></span>
              <span>VERIFIER: DR. ELENA VANCE</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-xl border border-white/10 hover:border-white/20 text-[11px] font-mono text-[#8e9e94] hover:text-white transition"
            >
              DISCONNECT
            </button>
          </div>
        </div>
      </header>

      {/* Main Content View Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 lg:px-12 py-10">
        {currentView === 'projects' && (
          <Projects
            onSelectProject={(p) => {
              setSelectedProject(p);
              setCurrentView('passport');
            }}
          />
        )}
        {currentView === 'passport' && selectedProject && (
          <ProcessPassport project={selectedProject} />
        )}
        {currentView === 'batch_import' && <BatchImport />}
        {currentView === 'vessels' && <Vessels />}
        {currentView === 'scenario' && (
          <ScenarioBuilder
            onAssessmentCompleted={(ass) => {
              setLatestAssessment(ass);
              setCurrentView('assessment');
            }}
          />
        )}
        {currentView === 'assessment' && latestAssessment && (
          <AssessmentResults
            assessment={latestAssessment}
            onGenerateReport={() => setCurrentView('report')}
          />
        )}
        {currentView === 'report' && latestAssessment && (
          <Report
            assessment={latestAssessment}
            onBack={() => setCurrentView('assessment')}
          />
        )}
      </main>

      {/* Bottom Editorial Footer */}
      <footer className="border-t border-white/5 py-8 px-6 lg:px-12 text-xs font-mono text-[#708076]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-[#2fe578]">SCALEBRIDGE BIO</span>
            <span>//</span>
            <span>IMMUTABLE BIOPHYSICAL CONSENSUS</span>
          </div>
          <div>ESTABLISHED UNDER SOVEREIGN CUSTODY RULES</div>
        </div>
      </footer>
    </div>
  );
}
