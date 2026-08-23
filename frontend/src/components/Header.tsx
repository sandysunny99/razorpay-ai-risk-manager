import React from 'react';
import { ShieldCheck, Lock, RefreshCw, Cpu, Database, Eye } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  systemStatus: string;
  dryRun: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isLoading, systemStatus, dryRun }) => {
  return (
    <header className="border-b border-slate-800 bg-[#0B192C] px-6 py-4 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Tagline */}
        <div className="flex items-center space-x-4">
          <div className="h-11 w-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                RAZORPAY <span className="text-blue-400 font-semibold">AI RISK MANAGER</span>
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                v2.0.0-rc1
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                DEMO / TEST MODE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Broad Risk Detection (88.06% Recall) • Policy-Controlled Auto-Action (100% Precision) • Defense-in-Depth
            </p>
          </div>
        </div>

        {/* Status Indicators & Subsystem Badges */}
        <div className="flex items-center space-x-2.5">
          <div className="hidden lg:flex items-center space-x-2 text-[11px] font-mono text-slate-400">
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
              Cloudflare: <strong className="text-indigo-400 font-semibold">SIMULATED</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
              Razorpay: <strong className="text-amber-400 font-semibold">TEST/MOCK</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
              CTI: <strong className="text-purple-400 font-semibold">SYNTHETIC</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
              DLP: <strong className="text-emerald-400 font-semibold">VALIDATED</strong>
            </span>
          </div>

          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            {systemStatus}
          </span>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition disabled:opacity-50"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
