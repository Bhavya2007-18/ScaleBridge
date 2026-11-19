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
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <DemoDataBanner />
      
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentView('projects')}>
            <span className="w-8 h-8 rounded-lg bg-indigo-600 text-white font-black flex items-center justify-center text-sm">
              SB
            </span>
            <span className="font-bold text-slate-900 tracking-tight text-lg">ScaleBridge Bio</span>
          </div>

          <nav className="flex items-center gap-1 text-xs font-semibold text-slate-600">
            <button
              onClick={() => setCurrentView('projects')}
              className={`px-3 py-1.5 rounded-lg transition ${currentView === 'projects' ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100'}`}
            >
              Projects
            </button>
            {selectedProject && (
              <button
                onClick={() => setCurrentView('passport')}
                className={`px-3 py-1.5 rounded-lg transition ${currentView === 'passport' ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100'}`}
              >
                Passport
              </button>
            )}
            <button
              onClick={() => setCurrentView('vessels')}
              className={`px-3 py-1.5 rounded-lg transition ${currentView === 'vessels' ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100'}`}
            >
              Vessels
            </button>
            <button
              onClick={() => setCurrentView('batch_import')}
              className={`px-3 py-1.5 rounded-lg transition ${currentView === 'batch_import' ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100'}`}
            >
              Data Ingest
            </button>
            <button
              onClick={() => setCurrentView('scenario')}
              className={`px-3 py-1.5 rounded-lg transition ${currentView === 'scenario' ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100'}`}
            >
              Scenario Builder
            </button>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 font-medium">Dr. Elena Vance (Lead Scientist)</span>
          <button
            onClick={handleLogout}
            className="text-xs text-slate-500 hover:text-slate-800 font-semibold px-2 py-1"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main View Area */}
      <main className="flex-1">
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
    </div>
  );
}
