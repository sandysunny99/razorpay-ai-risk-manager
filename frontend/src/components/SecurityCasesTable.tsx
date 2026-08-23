import React from 'react';
import { FolderKanban, ShieldCheck, Clock, UserCheck } from 'lucide-react';
import { SecurityCase } from '../types';

interface SecurityCasesTableProps {
  cases: SecurityCase[];
}

export const SecurityCasesTable: React.FC<SecurityCasesTableProps> = ({ cases }) => {
  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderKanban className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-bold text-white tracking-tight">
            SOC SECURITY CASE QUEUE
          </h3>
        </div>
        <span className="text-xs text-slate-400">Automated Case Dispatch</span>
      </div>

      {cases.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-xs border border-slate-800/80 rounded-xl bg-slate-900/30">
          No security cases currently open. Trigger an investigation to auto-create incidents.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Risk Score</th>
                <th className="px-4 py-3">Assigned Handler</th>
                <th className="px-4 py-3">Actions Taken</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {cases.map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-mono font-bold text-purple-300">{c.case_id}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        c.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {c.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-bold text-rose-400">{c.risk_score}</td>
                  <td className="px-4 py-3 text-slate-300 flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-blue-400" />
                    <span>{c.assigned_to}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {c.actions_taken?.map((act, i) => (
                        <span
                          key={i}
                          className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700 font-mono"
                        >
                          {act}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-400">
                    {new Date(c.created_at).toLocaleTimeString()}
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
