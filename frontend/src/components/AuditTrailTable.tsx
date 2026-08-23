import React from 'react';
import { History, ShieldCheck, CheckCircle2, Lock } from 'lucide-react';
import { AuditEvent } from '../types';

interface AuditTrailTableProps {
  events: AuditEvent[];
}

export const AuditTrailTable: React.FC<AuditTrailTableProps> = ({ events }) => {
  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-bold text-white tracking-tight">
            IMMUTABLE SECURITY AUDIT TRAIL
          </h3>
        </div>
        <span className="text-xs text-slate-400">Cryptographically Recorded Decisions</span>
      </div>

      {events.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-xs border border-slate-800/80 rounded-xl bg-slate-900/30">
          Zero audit records present. Remediation actions will log cryptographic proof here.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="px-4 py-3">Audit Event ID</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Policy Evaluated</th>
                <th className="px-4 py-3">Action Executed</th>
                <th className="px-4 py-3">Verification Result</th>
                <th className="px-4 py-3">Risk Assessment</th>
                <th className="px-4 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {events.map((e) => (
                <tr key={e.event_id} className="hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-mono font-bold text-emerald-400">{e.event_id}</td>
                  <td className="px-4 py-3 font-medium text-white">{e.actor}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {e.policy_evaluated}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-200">{e.action_executed || 'MONITOR'}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {e.verification_result || 'VERIFIED'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-bold text-rose-400">{e.risk_score}/100</td>
                  <td className="px-4 py-3 font-mono text-slate-400">
                    {new Date(e.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
