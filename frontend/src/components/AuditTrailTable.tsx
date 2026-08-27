import React, { useState } from 'react';
import { History, ShieldCheck, CheckCircle2, AlertTriangle, Link2, RefreshCw } from 'lucide-react';
import { AuditEvent } from '../types';
import { api } from '../services/api';
import { Pagination } from './Pagination';
import { TableSkeleton } from './Skeleton';

interface AuditTrailTableProps {
  events: AuditEvent[];
  isLoading?: boolean;
}

export const AuditTrailTable: React.FC<AuditTrailTableProps> = ({ events, isLoading }) => {
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const PAGE_SIZE = 10;

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    try {
      const result = await api.verifyAuditChain();
      setVerificationResult(result);
    } catch (err) {
      console.error('Verification failed', err);
    } finally {
      setIsVerifying(false);
    }
  };

  if (isLoading) {
    return <TableSkeleton rows={8} />;
  }

  const paginatedEvents = events.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              TAMPER-EVIDENT HASH-CHAINED AUDIT LEDGER
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Cryptographically linked blocks: <span className="font-mono text-emerald-400">curr_hash = SHA256(data + prev_hash)</span>
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={isVerifying || events.length === 0}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 text-xs font-semibold border border-emerald-500/40 transition disabled:opacity-50"
        >
          {isVerifying ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Link2 className="w-3.5 h-3.5" />
          )}
          <span>Verify Hash Chain Integrity</span>
        </button>
      </div>

      {verificationResult && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
            verificationResult.valid
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
              : 'bg-rose-950/30 border-rose-500/40 text-rose-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {verificationResult.valid ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            )}
            <span className="font-semibold">
              {verificationResult.valid
                ? `Cryptographic Proof Confirmed: ${verificationResult.total_events} blocks validated with 0 tampering detected.`
                : `WARNING: Tampering detected across ${verificationResult.tampered_events.length} blocks!`}
            </span>
          </div>
          {verificationResult.head_hash && (
            <span className="font-mono text-[10px] text-slate-400 truncate max-w-xs">
              Head: {verificationResult.head_hash.slice(0, 16)}...
            </span>
          )}
        </div>
      )}

      {events.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-xs border border-slate-800/80 rounded-xl bg-slate-900/30">
          Zero audit records present. Remediation actions will log cryptographic proof here.
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
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
                {paginatedEvents.map((e) => (
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
          {events.length > PAGE_SIZE && (
            <Pagination
              currentPage={currentPage}
              totalItems={events.length}
              pageSize={PAGE_SIZE}
              onPageChange={setCurrentPage}
            />
          )}
        </div>
      )}
    </div>
  );
};
