import React from 'react';
import { ShieldCheck, ShieldAlert, Cpu, Lock, RefreshCw } from 'lucide-react';

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
                RAZORPAY <span className="text-blue-400 font-semibold">RISK MANAGER AGENT</span>
              </h1>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                Agentic v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Agentic security layer for payment risk, card exposure, token protection & controlled remediation
            </p>
          </div>
        </div>

        {/* Status Indicators & Refresh */}
        <div className="flex items-center space-x-3">
          {dryRun && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
              <Lock className="w-3.5 h-3.5" />
              DRY_RUN PROTECTED
            </span>
          )}

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
