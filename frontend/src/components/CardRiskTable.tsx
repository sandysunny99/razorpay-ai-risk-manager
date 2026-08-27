import React from 'react';
import { CreditCard, Search, ShieldAlert } from 'lucide-react';
import { TableSkeleton } from './Skeleton';
import { CardItem } from '../types';

interface CardRiskTableProps {
  cards: CardItem[];
  onInvestigateCard: (cardId: string) => void;
  isInvestigating?: boolean;
  isLoading?: boolean;
}

export const CardRiskTable: React.FC<CardRiskTableProps> = ({
  cards,
  onInvestigateCard,
  isInvestigating,
  isLoading,
}) => {
  if (isLoading) {
    return <TableSkeleton rows={6} />;
  }
  const getRiskBadge = (score: number) => {
    if (score >= 75) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
          {score} • CRITICAL
        </span>
      );
    }
    if (score >= 50) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
          {score} • HIGH
        </span>
      );
    }
    if (score >= 25) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
          {score} • MEDIUM
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
        {score} • LOW
      </span>
    );
  };

  return (
    <div className="bg-[#0B192C] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-bold text-white tracking-tight">
            MONITORED CARDS & EXPOSURE INVENTORY
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          HMAC-SHA-256 Fingerprinted • PCI-Aware Prototype
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
            <tr>
              <th className="px-4 py-3">Masked PAN</th>
              <th className="px-4 py-3">BIN</th>
              <th className="px-4 py-3">Cardholder</th>
              <th className="px-4 py-3">Expiry</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Breach Exposure</th>
              <th className="px-4 py-3">Active Tokens</th>
              <th className="px-4 py-3">Risk Assessment</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
            {cards.map((card) => (
              <tr key={card.card_id} className="hover:bg-slate-800/30 transition">
                <td className="px-4 py-3 font-mono font-bold text-white">{card.masked_pan}</td>
                <td className="px-4 py-3 font-mono text-slate-400">{card.bin}</td>
                <td className="px-4 py-3 text-slate-200">{card.cardholder_name}</td>
                <td className="px-4 py-3 font-mono text-slate-400">
                  {String(card.expiry_month).padStart(2, '0')}/{card.expiry_year}
                  {card.is_expired && (
                    <span className="ml-1 text-[10px] text-rose-400 font-semibold">(Expired)</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      card.status === 'ACTIVE'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    {card.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {card.exposure_count > 0 ? (
                    <span className="inline-flex items-center gap-1 text-rose-400 font-semibold">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      {card.exposure_count} Leaks Found
                    </span>
                  ) : (
                    <span className="text-slate-500">Clean</span>
                  )}
                </td>
                <td className="px-4 py-3 font-mono text-slate-300">{card.active_token_count} Vault Tokens</td>
                <td className="px-4 py-3">{getRiskBadge(card.current_risk_score)}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onInvestigateCard(card.card_id)}
                    disabled={isInvestigating}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 hover:text-blue-300 border border-blue-500/30 text-[11px] font-medium transition disabled:opacity-50"
                  >
                    <Search className="w-3 h-3" />
                    Investigate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
