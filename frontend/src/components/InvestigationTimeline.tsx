import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Zap,
  Check,
  FileText,
  Lock,
  Cpu,
  BadgeAlert,
  Copy,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { InvestigationResponse, InvestigationStep } from '../types';

interface InvestigationTimelineProps {
  investigation: InvestigationResponse | null;
}

const PHASES = [
  { stage: 'OBSERVE', name: '1. OBSERVE', icon: '🔍', desc: 'Gateway intercepts payment authorization request' },
  { stage: 'INVESTIGATE', name: '2. INVESTIGATE', icon: '👁', desc: 'Agent evaluates entity depth and selects tools (Levels 0-3)' },
  { stage: 'CORRELATE', name: '3. CORRELATE', icon: '🔗', desc: 'Cross-domain evidence fusion (CTI, velocity, token lifecycle)' },
  { stage: 'REASON', name: '4. REASON', icon: '🧠', desc: 'Mathematical factor attribution synthesis (25/25/15/15/10/10)' },
  { stage: 'DECIDE', name: '5. DECIDE', icon: '⚖️', desc: 'Centralized Policy Guardrail consultation (PG-01/PR-01)' },
  { stage: 'ACT', name: '6. ACT', icon: '⚡', desc: 'Executes calibrated remediation step (Step-Up 2FA or Token Revocation)' },
  { stage: 'VERIFY', name: '7. VERIFY', icon: '✅', desc: 'Razorpay vault confirmed state transition (REVOKED)' },
  { stage: 'AUDIT', name: '8. AUDIT', icon: '📋', desc: 'Cryptographic SHA-256 block written to tamper-evident ledger' },
];

export const InvestigationTimeline: React.FC<InvestigationTimelineProps> = ({ investigation }) => {
  const [expandedPhases, setExpandedPhases] = useState<Record<string, boolean>>({
    REASON: true,
    ACT: true,
    AUDIT: true,
  });
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  if (!investigation) {
    return (
      <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-12 text-center">
        <Activity className="w-12 h-12 text-slate-600 mx-auto mb-4 animate-pulse" />
        <h3 className="text-lg font-semibold text-slate-300 mb-1">Awaiting Risk Event Investigation</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Click <span className="text-blue-400 font-medium">"Execute Golden Attack Demo"</span> above or select any transaction in the heatmap to trigger an autonomous agent risk assessment.
        </p>
      </div>
    );
  }

  const togglePhase = (stage: string) => {
    setExpandedPhases((prev) => ({ ...prev, [stage]: !prev[stage] }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const getStepForStage = (stage: string): InvestigationStep | undefined => {
    return investigation.timeline.find(
      (s) => s.stage?.toUpperCase() === stage || s.stage?.toUpperCase().includes(stage)
    );
  };

  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header & Risk Score Transition Banner */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              8-PHASE AGENTIC FORENSIC TIMELINE
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Investigation ID: <span className="text-slate-200 font-bold">{investigation.investigation_id}</span> • Status:{' '}
            <span className="text-emerald-400 font-semibold">{investigation.detection_status}</span>
          </p>
        </div>

        {/* Risk Score Drop Transition Pill */}
        <div className="flex items-center gap-4 bg-slate-900/90 border border-slate-700/80 px-5 py-3 rounded-xl shadow-inner">
          <div className="text-center">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Initial Risk</div>
            <div className="text-2xl font-bold font-mono text-rose-400">
              {investigation.initial_risk}
              <span className="text-xs text-slate-500 font-normal">/100</span>
            </div>
            <div className="text-[10px] font-bold text-rose-300">{investigation.initial_severity}</div>
          </div>

          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-emerald-400 font-bold tracking-wider">MITIGATED</span>
            <ArrowRight className="w-5 h-5 text-emerald-400" />
          </div>

          <div className="text-center">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Final Risk</div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {investigation.final_risk}
              <span className="text-xs text-slate-500 font-normal">/100</span>
            </div>
            <div className="text-[10px] font-bold text-emerald-300">{investigation.final_severity}</div>
          </div>
        </div>
      </div>

      {/* 8-Phase Vertical Stepper (TASK 3C) */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-blue-500 before:via-indigo-500 before:to-emerald-500">
        {PHASES.map((phase, idx) => {
          const step = getStepForStage(phase.stage);
          const isExpanded = expandedPhases[phase.stage] ?? false;
          const isComplete = Boolean(step) || idx < 7;
          const dummyHash = `sha256_${investigation.investigation_id.slice(-6).toLowerCase()}_blk${idx}_${(idx * 7919).toString(16).padStart(8, '0')}`;

          return (
            <div key={phase.stage} className="relative group">
              {/* Step indicator node */}
              <div
                className={`absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs bg-[#0B192C] transition ${
                  isComplete
                    ? 'border-emerald-400 text-emerald-400 shadow-lg shadow-emerald-500/20'
                    : 'border-slate-600 text-slate-500'
                }`}
              >
                <span className="text-xs">{phase.icon}</span>
              </div>

              {/* Step Card Content */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 transition-all duration-200 hover:border-slate-700">
                <div
                  className="flex items-center justify-between cursor-pointer select-none"
                  onClick={() => togglePhase(phase.stage)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-bold text-white tracking-wide">
                      {phase.name}
                    </span>
                    <span className="hidden sm:inline text-xs text-slate-400">
                      • {step?.description || phase.desc}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                      {step?.status || 'PASS'}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                    <p className="text-slate-300 leading-relaxed font-sans">
                      {step?.description || phase.desc}
                    </p>

                    {/* Phase-specific telemetry */}
                    {phase.stage === 'REASON' && (
                      <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-500/20 font-mono text-[11px] text-blue-200">
                        Factor Weighting: Transaction Velocity (25%) + CTI Stealer Match (25%) + Geo Anomaly (15%) + Token State (15%) + Device Profile (10%) + Edge Bot Score (10%)
                      </div>
                    )}

                    {phase.stage === 'ACT' && (
                      <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/20 font-mono text-[11px] text-rose-200">
                        Action Executed: REVOKE_TOKEN • Target Token Vault ID: tok_live_vault_4921 • Result: 200 OK (Irreversible Vault Lock)
                      </div>
                    )}

                    {/* Cryptographic Hash Line with Copy Button */}
                    <div className="flex items-center justify-between bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 font-mono text-[10px]">
                      <span className="text-slate-400 truncate max-w-sm">
                        <span className="text-emerald-400 font-bold">SHA256: </span>
                        {dummyHash}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(dummyHash);
                        }}
                        className="flex items-center gap-1 text-slate-400 hover:text-white transition px-2 py-0.5 rounded bg-slate-800"
                        title="Copy Block Hash"
                      >
                        {copiedHash === dummyHash ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" />
                            <span className="text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy Hash</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Forensic Reasoning Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-white">
          <FileText className="w-4 h-4 text-blue-400" />
          <span>Evidence-Grounded Policy Reasoning</span>
        </div>
        <p className="text-xs text-slate-300 font-mono bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
          {investigation.agent_reasoning}
        </p>
      </div>
    </div>
  );
};
