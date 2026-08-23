import React from 'react';
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
} from 'lucide-react';
import { InvestigationResponse } from '../types';

interface InvestigationTimelineProps {
  investigation: InvestigationResponse | null;
}

export const InvestigationTimeline: React.FC<InvestigationTimelineProps> = ({ investigation }) => {
  if (!investigation) {
    return (
      <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-12 text-center">
        <Activity className="w-12 h-12 text-slate-600 mx-auto mb-4 animate-pulse" />
        <h3 className="text-lg font-semibold text-slate-300 mb-1">Awaiting Risk Event Investigation</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Click <span className="text-blue-400 font-medium">"Execute Golden Attack Demo"</span> above to trigger an autonomous agent risk assessment.
        </p>
      </div>
    );
  }

  const getStageColor = (stage: string, status: string) => {
    if (status === 'WARNING') return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    if (status === 'SUCCESS') return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (status === 'FAILED') return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
  };

  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header & Risk Score Transition Banner */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              AGENT INVESTIGATION TIMELINE
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Investigation ID: <span className="font-mono text-slate-300">{investigation.investigation_id}</span>
          </p>
        </div>

        {/* Risk Score Drop Pill */}
        <div className="flex items-center gap-4 bg-slate-900/80 border border-slate-700/80 px-5 py-3 rounded-xl shadow-inner">
          <div className="text-center">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Initial Risk</div>
            <div className="text-2xl font-black text-rose-400 flex items-center gap-1">
              <span>{investigation.initial_risk}</span>
              <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                {investigation.initial_severity}
              </span>
            </div>
          </div>

          <div className="flex flex-col items-center justify-center text-slate-500">
            <span className="text-[10px] uppercase font-bold text-blue-400">Remediated</span>
            <ArrowRight className="w-5 h-5 text-blue-400 stroke-[2.5]" />
          </div>

          <div className="text-center">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Verified Final Risk</div>
            <div className="text-2xl font-black text-emerald-400 flex items-center gap-1">
              <span>{investigation.final_risk}</span>
              <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                {investigation.final_severity}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Verified Action, Policy & Tier Badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Detection Status</div>
          <div className={`text-xs font-bold font-mono mt-0.5 ${investigation.detection_status === 'SUSPICIOUS' ? 'text-amber-400' : 'text-emerald-400'}`}>
            {investigation.detection_status || 'CLEAN'}
          </div>
          <span className="text-[9px] text-slate-500">Broad Detection Layer</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Response Tier</div>
          <div className="text-xs font-bold text-blue-400 font-mono mt-0.5">
            {investigation.response_tier || 'LOW'}
          </div>
          <span className="text-[9px] text-slate-500">Level {investigation.investigation_level || 0} Investigation</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Policy Decision</div>
          <div className="text-xs font-bold text-white font-mono mt-0.5 truncate">
            {investigation.policy_decision || investigation.policy_status}
          </div>
          <span className="text-[9px] text-slate-500">{investigation.recommended_action}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Gateway Verification</div>
          <div className="text-xs font-bold text-emerald-400 font-mono mt-0.5 truncate">
            {investigation.verification_status}
          </div>
          <span className="text-[9px] text-slate-500">{investigation.case_id || 'No Case Required'}</span>
        </div>
      </div>

      {/* Dynamic Tool Selection Audit */}
      {investigation.tool_audit && investigation.tool_audit.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Dynamic Agent Tool Selection & Audit ({investigation.tools_executed?.length || 0} executed, {investigation.tools_skipped?.length || 0} skipped)
            </h4>
            <span className="text-[10px] font-mono text-blue-400">Contextual Efficiency</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {investigation.tool_audit.map((t, idx) => (
              <div key={idx} className={`p-2 rounded-lg border text-[11px] flex items-start justify-between gap-2 ${t.selected ? 'bg-slate-900/70 border-slate-700' : 'bg-slate-950/40 border-slate-800/60 opacity-60'}`}>
                <div>
                  <span className={`font-mono font-bold ${t.selected ? 'text-blue-300' : 'text-slate-500'}`}>
                    {t.tool}()
                  </span>
                  <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">{t.reason}</p>
                </div>
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${t.selected ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}`}>
                  {t.selected ? 'EXECUTED' : 'SKIPPED'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step-by-Step Investigation Trail */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Chronological Agent Execution Sequence
        </h4>
        <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {investigation.timeline.map((step, idx) => (
            <div key={idx} className="relative group">
              {/* Bullet Node */}
              <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#0B192C] border-2 border-blue-500 flex items-center justify-center shadow">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
              </div>

              {/* Step Card */}
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStageColor(step.stage, step.status)}`}>
                      {step.stage}
                    </span>
                    {step.tool_used && (
                      <span className="text-[11px] text-slate-400 font-mono">
                        tool: <span className="text-blue-300">{step.tool_used}()</span>
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">{step.timestamp}</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Reasoning Box */}
      <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/30">
        <div className="flex items-center gap-2 mb-1.5">
          <Check className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-bold text-blue-300 uppercase tracking-wide">
            Autonomous Agent Reasoning Summary
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{investigation.agent_reasoning}</p>
      </div>

      {/* Explainable Factor Contribution Table */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Explainable Multi-Dimensional Risk Factors
        </h4>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="px-3.5 py-2.5">Risk Dimension</th>
                <th className="px-3.5 py-2.5">Weight</th>
                <th className="px-3.5 py-2.5">Raw Score</th>
                <th className="px-3.5 py-2.5">Contribution</th>
                <th className="px-3.5 py-2.5">Reason & Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {investigation.explainable_factors.map((f, i) => (
                <tr key={i} className="hover:bg-slate-800/30 transition">
                  <td className="px-3.5 py-2.5 font-medium text-white">{f.name}</td>
                  <td className="px-3.5 py-2.5 font-mono text-slate-400">{f.weight}%</td>
                  <td className="px-3.5 py-2.5 font-mono">
                    <span className={f.score >= 50 ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                      {f.score}
                    </span>
                  </td>
                  <td className="px-3.5 py-2.5 font-mono text-blue-300 font-semibold">+{f.contribution}</td>
                  <td className="px-3.5 py-2.5 text-slate-400 max-w-xs truncate" title={f.reason}>
                    {f.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
