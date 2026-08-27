import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { EvaluationTransactionItem } from '../types';
import { api } from '../services/api';

interface LiveRiskTableProps {
  onInvestigateTransaction?: (txnId: string) => void;
  isInvestigating?: boolean;
}

export const LiveRiskTable: React.FC<LiveRiskTableProps> = ({
  onInvestigateTransaction,
  isInvestigating = false,
}) => {
  const [transactions, setTransactions] = useState<EvaluationTransactionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [split, setSplit] = useState<string>('test.jsonl');

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const data = await api.getEvaluationTransactions(split, 25);
      setTransactions(data.transactions || []);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [split]);

  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              RISK SCREENING STREAM
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                SIMULATION MODE
              </span>
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Transaction stream correlated with CTI feeds, token state, and velocity
          </p>
        </div>

        <select
          value={split}
          onChange={(e) => setSplit(e.target.value)}
          className="bg-slate-900 border border-slate-700 text-xs font-mono text-white rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500"
        >
          <option value="test.jsonl">Held-Out Test Stream (300 records)</option>
          <option value="validation.jsonl">Validation Stream (300 records)</option>
          <option value="train.jsonl">Training Stream (1,400 records)</option>
        </select>
      </div>

      {/* Simulation Mode Banner */}
      <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs font-mono">
        <span>⚡</span>
        <span>Demo environment — 5 deterministic golden scenarios. In production, events stream from Razorpay webhook endpoint.</span>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Loading live transaction stream...
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="px-4 py-3">Txn ID</th>
                <th className="px-4 py-3">Masked Card</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Geo Origin</th>
                <th className="px-4 py-3">Velocity (10m)</th>
                <th className="px-4 py-3">Threat Exposure</th>
                <th className="px-4 py-3">Token State</th>
                <th className="px-4 py-3">Risk Score</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {transactions.map((t) => (
                <tr key={t.transaction_id} className="hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-mono font-bold text-blue-400">{t.transaction_id}</td>
                  <td className="px-4 py-3 font-mono text-slate-300">{t.card_masked}</td>
                  <td className="px-4 py-3 font-mono font-bold text-white">₹{t.amount.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                      t.country !== t.customer_country
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-slate-800 text-slate-300'
                    }`}>
                      {t.country} {t.country !== t.customer_country && '(Mismatch)'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">
                    <span className={t.velocity_10m >= 3 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                      {t.velocity_10m} attempts
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {t.card_exposed ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {t.exposure_source} ({(t.exposure_confidence * 100).toFixed(0)}%)
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500">None</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {t.is_zombie_token ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        ZOMBIE
                      </span>
                    ) : t.token_active ? (
                      <span className="text-emerald-400 text-[11px]">ACTIVE</span>
                    ) : (
                      <span className="text-slate-500 text-[11px]">INACTIVE</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      t.calculated_risk_score >= 75.0
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : t.calculated_risk_score >= 50.0
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/10 text-emerald-400'
                    }`}>
                      {t.calculated_risk_score}/100 [{t.severity}]
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onInvestigateTransaction && onInvestigateTransaction(t.transaction_id)}
                      disabled={isInvestigating}
                      className="flex items-center gap-1 text-[11px] font-semibold text-blue-400 hover:text-blue-300 transition"
                    >
                      <span>Investigate</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
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
