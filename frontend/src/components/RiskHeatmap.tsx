import React, { useState } from 'react';
import { Grid, ShieldAlert, AlertTriangle, CheckCircle2, Search } from 'lucide-react';

export interface HeatmapTransaction {
  id: string;
  cardId: string;
  amount: number;
  riskScore: number;
  tier: 'ALLOW' | 'MONITOR' | 'STEP_UP' | 'REVIEW' | 'AUTO_REMEDIATE';
  timestamp: string;
  location: string;
}

interface RiskHeatmapProps {
  transactions?: HeatmapTransaction[];
  onSelectTransaction?: (txnId: string) => void;
}

// Generate deterministic 100 transactions if not supplied
const generateDefaultTransactions = (): HeatmapTransaction[] => {
  const tiers: HeatmapTransaction['tier'][] = ['ALLOW', 'MONITOR', 'STEP_UP', 'REVIEW', 'AUTO_REMEDIATE'];
  const cities = ['Bengaluru', 'Mumbai', 'Delhi', 'Hyderabad', 'Pune', 'Chennai'];

  return Array.from({ length: 100 }, (_, idx) => {
    // Generate realistic distribution (most low risk, few high risk)
    let score = Math.floor(Math.random() * 35);
    if (idx % 12 === 0) score = 75 + Math.floor(Math.random() * 24); // Critical
    else if (idx % 5 === 0) score = 40 + Math.floor(Math.random() * 30); // Elevated
    else if (idx % 4 === 0) score = 35 + Math.floor(Math.random() * 5); // Monitor

    let tier: HeatmapTransaction['tier'] = 'ALLOW';
    if (score >= 75) tier = 'AUTO_REMEDIATE';
    else if (score >= 65) tier = 'REVIEW';
    else if (score >= 40) tier = 'STEP_UP';
    else if (score >= 35) tier = 'MONITOR';

    return {
      id: `TXN-2026-${(9000 + idx).toString()}`,
      cardId: `card_test_${(1000 + (idx % 15)).toString()}`,
      amount: 500 + Math.floor(Math.random() * 25000),
      riskScore: score,
      tier,
      timestamp: `${Math.floor(idx / 4)}m ago`,
      location: cities[idx % cities.length],
    };
  });
};

export const RiskHeatmap: React.FC<RiskHeatmapProps> = ({
  transactions,
  onSelectTransaction,
}) => {
  const [data] = useState<HeatmapTransaction[]>(
    transactions && transactions.length > 0 ? transactions : generateDefaultTransactions()
  );
  const [hoveredTxn, setHoveredTxn] = useState<HeatmapTransaction | null>(null);
  const [filterTier, setFilterTier] = useState<string>('ALL');

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'bg-rose-500 hover:bg-rose-400 border-rose-400/50';
    if (score >= 65) return 'bg-orange-500 hover:bg-orange-400 border-orange-400/50';
    if (score >= 40) return 'bg-amber-500 hover:bg-amber-400 border-amber-400/50';
    if (score >= 35) return 'bg-blue-500 hover:bg-blue-400 border-blue-400/50';
    return 'bg-emerald-600/80 hover:bg-emerald-500 border-emerald-400/30';
  };

  const filtered = filterTier === 'ALL' ? data : data.filter((t) => t.tier === filterTier);
  const criticalCount = data.filter((t) => t.riskScore >= 75).length;
  const elevatedCount = data.filter((t) => t.riskScore >= 40 && t.riskScore < 75).length;
  const nominalCount = data.filter((t) => t.riskScore < 40).length;

  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
      {/* Header & Metric Summary */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Grid className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              100-TRANSACTION RISK HEATMAP MATRIX
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Real-time multi-factor matrix visualization • Hover cell for forensic inspection
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1 text-[11px] font-mono bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setFilterTier('ALL')}
            className={`px-2.5 py-1 rounded-lg transition ${
              filterTier === 'ALL' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            All (100)
          </button>
          <button
            onClick={() => setFilterTier('AUTO_REMEDIATE')}
            className={`px-2.5 py-1 rounded-lg transition ${
              filterTier === 'AUTO_REMEDIATE'
                ? 'bg-rose-600 text-white font-bold'
                : 'text-rose-400 hover:bg-rose-500/10'
            }`}
          >
            Critical ({criticalCount})
          </button>
          <button
            onClick={() => setFilterTier('STEP_UP')}
            className={`px-2.5 py-1 rounded-lg transition ${
              filterTier === 'STEP_UP'
                ? 'bg-amber-600 text-white font-bold'
                : 'text-amber-400 hover:bg-amber-500/10'
            }`}
          >
            Elevated ({elevatedCount})
          </button>
          <button
            onClick={() => setFilterTier('ALLOW')}
            className={`px-2.5 py-1 rounded-lg transition ${
              filterTier === 'ALLOW'
                ? 'bg-emerald-600 text-white font-bold'
                : 'text-emerald-400 hover:bg-emerald-500/10'
            }`}
          >
            Nominal ({nominalCount})
          </button>
        </div>
      </div>

      {/* Main Heatmap Grid & Tooltip Dock */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
        {/* 10x10 Matrix */}
        <div className="lg:col-span-2 bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 shadow-inner">
          <div className="grid grid-cols-10 gap-1.5 sm:gap-2 aspect-square max-w-lg mx-auto">
            {filtered.slice(0, 100).map((txn) => {
              const isCritical = txn.riskScore >= 75;
              const isHovered = hoveredTxn?.id === txn.id;
              return (
                <button
                  key={txn.id}
                  onMouseEnter={() => setHoveredTxn(txn)}
                  onClick={() => onSelectTransaction?.(txn.id)}
                  className={`relative rounded-md aspect-square border transition-all duration-150 transform hover:scale-125 hover:z-20 cursor-pointer ${getScoreColor(
                    txn.riskScore
                  )} ${isCritical ? 'animate-pulse' : ''} ${isHovered ? 'ring-2 ring-white shadow-lg' : ''}`}
                  title={`${txn.id} • Score: ${txn.riskScore}`}
                />
              );
            })}
          </div>
        </div>

        {/* Dynamic Forensic Inspector Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-mono text-slate-400">HOVERED TRANSACTION</span>
            {hoveredTxn && (
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  hoveredTxn.riskScore >= 75
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : hoveredTxn.riskScore >= 40
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}
              >
                {hoveredTxn.tier}
              </span>
            )}
          </div>

          {hoveredTxn ? (
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">TXN ID:</span>
                <span className="text-white font-bold">{hoveredTxn.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Card ID:</span>
                <span className="text-blue-400">{hoveredTxn.cardId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Amount:</span>
                <span className="text-white">₹{hoveredTxn.amount.toLocaleString('en-IN')}.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Location:</span>
                <span className="text-slate-200">{hoveredTxn.location}, IN</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Risk Score:</span>
                <span
                  className={`text-sm font-bold ${
                    hoveredTxn.riskScore >= 75
                      ? 'text-rose-400'
                      : hoveredTxn.riskScore >= 40
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {hoveredTxn.riskScore}/100
                </span>
              </div>

              <button
                onClick={() => onSelectTransaction?.(hoveredTxn.id)}
                className="w-full mt-2 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-sans text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-lg shadow-blue-500/20"
              >
                <Search className="w-3.5 h-3.5" />
                Launch Full Agent Investigation
              </button>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500 font-mono">
              Hover over any matrix block to view forensic signal telemetry.
            </div>
          )}

          {/* Color Scale Legend */}
          <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-emerald-500" /> &lt;35 ALLOW
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-blue-500" /> 35-39 MON
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-amber-500" /> 40-74 STEP
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-rose-500" /> ≥75 REVOKE
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
