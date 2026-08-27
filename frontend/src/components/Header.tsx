import React from 'react';
import { ShieldCheck, RefreshCw, Command, HelpCircle } from 'lucide-react';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  systemStatus: string;
  dryRun: boolean;
  globalThreatScore?: number;
  onOpenShortcuts?: () => void;
  onOpenCommandPalette?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onRefresh,
  isLoading,
  systemStatus,
  globalThreatScore = 82,
  onOpenShortcuts,
  onOpenCommandPalette,
}) => {
  const getThreatBadge = (score: number) => {
    if (score >= 75) {
      return {
        label: 'CRITICAL',
        barColor: 'bg-rose-500',
        textColor: 'text-rose-400',
        borderColor: 'border-rose-500/40',
        bgColor: 'bg-rose-500/10',
        pulse: true,
      };
    }
    if (score >= 40) {
      return {
        label: 'ELEVATED',
        barColor: 'bg-amber-500',
        textColor: 'text-amber-400',
        borderColor: 'border-amber-500/40',
        bgColor: 'bg-amber-500/10',
        pulse: false,
      };
    }
    return {
      label: 'NOMINAL',
      barColor: 'bg-emerald-500',
      textColor: 'text-emerald-400',
      borderColor: 'border-emerald-500/40',
      bgColor: 'bg-emerald-500/10',
      pulse: false,
    };
  };

  const threat = getThreatBadge(globalThreatScore);

  return (
    <header className="border-b border-slate-800 bg-[#0B192C] px-6 py-3.5 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand & Tagline */}
        <div className="flex items-center space-x-4">
          <div className="h-11 w-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 flex-shrink-0">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                RAZORPAY <span className="text-blue-400 font-semibold">AI RISK MANAGER</span>
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                v2.1.0
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                DEMO / TEST MODE
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Broad Detection (88.06% Recall) • Policy-Controlled Auto-Action (100% Precision) • Defense-in-Depth
            </p>
          </div>
        </div>

        {/* Global Threat Meter (TASK 3D) & Subsystem Badges */}
        <div className="flex items-center space-x-3 w-full md:w-auto justify-between md:justify-end">
          {/* Global Threat Bar */}
          <div
            className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl border ${threat.borderColor} ${threat.bgColor} backdrop-blur-sm shadow-inner`}
          >
            <div className="flex flex-col">
              <div className="flex items-center justify-between gap-2 text-[10px] font-mono">
                <span className="text-slate-400 font-semibold">GLOBAL THREAT</span>
                <span className={`font-bold ${threat.textColor}`}>
                  {globalThreatScore}/100 {threat.label}
                </span>
              </div>
              <div className="w-28 h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
                <div
                  className={`h-full ${threat.barColor} transition-all duration-500 ${
                    threat.pulse ? 'animate-pulse' : ''
                  }`}
                  style={{ width: `${Math.min(100, Math.max(0, globalThreatScore))}%` }}
                />
              </div>
            </div>
          </div>

          <div className="hidden xl:flex items-center space-x-1.5 text-[11px] font-mono text-slate-400">
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
              OTel: <strong className="text-emerald-400">TRACING</strong>
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
              Razorpay: <strong className="text-amber-400">WEBHOOKS</strong>
            </span>
          </div>

          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            {systemStatus}
          </span>

          {/* Quick Actions (Command Palette & Shortcuts) */}
          <div className="flex items-center gap-1">
            <button
              onClick={onOpenCommandPalette}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
              title="Command Palette (Ctrl+K / ⌘K)"
            >
              <Command className="w-4 h-4" />
            </button>

            <button
              onClick={onOpenShortcuts}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
              title="Keyboard Shortcuts (?)"
            >
              <HelpCircle className="w-4 h-4" />
            </button>

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
      </div>
    </header>
  );
};
