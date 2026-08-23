import React, { useState } from 'react';
import { Play, Sparkles, RotateCcw, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { ScenarioItem } from '../types';

interface DemoScenarioTriggerProps {
  onTriggerGoldenDemo: () => void;
  onResetData: () => void;
  scenarios: ScenarioItem[];
  isRunning: boolean;
}

export const DemoScenarioTrigger: React.FC<DemoScenarioTriggerProps> = ({
  onTriggerGoldenDemo,
  onResetData,
  scenarios,
  isRunning,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>('golden_compromise');

  return (
    <div className="bg-[#0F2238] border border-blue-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">
              AGENTIC RISK WORKFLOW CONTROLLER
            </h2>
          </div>
          <p className="text-sm text-slate-300 max-w-2xl">
            Simulate live payment attacks, zero-knowledge threat correlation, policy evaluation, and verified token remediation.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onResetData}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium border border-slate-700 transition disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" />
            Reset State
          </button>

          <button
            onClick={onTriggerGoldenDemo}
            disabled={isRunning}
            className="flex items-center gap-2.5 px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/25 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Agent Investigating Attack...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Execute Golden Attack Demo (₹18,500)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Scenario Explainer Card */}
      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
        {scenarios.map((sc) => (
          <div
            key={sc.id}
            onClick={() => setSelectedScenario(sc.id)}
            className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
              selectedScenario === sc.id
                ? 'bg-blue-900/30 border-blue-500/60 ring-1 ring-blue-500/40'
                : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-white truncate">{sc.name}</span>
              {sc.id === 'golden_compromise' && (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  CRITICAL
                </span>
              )}
              {sc.id === 'zombie_token_scan' && (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  ZOMBIE
                </span>
              )}
              {sc.id === 'clean_transaction' && (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  CLEAN
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{sc.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
