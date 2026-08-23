import React from 'react';
import { CreditCard, KeyRound, Skull, AlertOctagon, ShieldAlert, FolderKanban } from 'lucide-react';
import { OverviewMetrics } from '../types';

interface RiskOverviewCardsProps {
  metrics: OverviewMetrics | null;
}

export const RiskOverviewCards: React.FC<RiskOverviewCardsProps> = ({ metrics }) => {
  const cards = [
    {
      title: 'Cards Monitored',
      value: metrics?.cards_monitored ?? 0,
      icon: CreditCard,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10 border-blue-500/20',
      subtitle: 'HMAC Zero-Knowledge Protected',
    },
    {
      title: 'Tokens Monitored',
      value: metrics?.tokens_monitored ?? 0,
      icon: KeyRound,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10 border-indigo-500/20',
      subtitle: 'Vault Managed Tokens',
    },
    {
      title: 'Active Zombie Tokens',
      value: metrics?.active_zombie_tokens ?? 0,
      icon: Skull,
      color: 'text-rose-400',
      bgColor: 'bg-rose-500/10 border-rose-500/30 ring-1 ring-rose-500/20',
      subtitle: 'Active Tokens on Dead Cards',
      alert: true,
    },
    {
      title: 'Exposure Events',
      value: metrics?.exposure_events_count ?? 0,
      icon: AlertOctagon,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10 border-amber-500/20',
      subtitle: 'Stealer Logs & Paste Matches',
    },
    {
      title: 'Critical Incidents',
      value: metrics?.critical_incidents ?? 0,
      icon: ShieldAlert,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10 border-red-500/20',
      subtitle: 'Remediation Required',
    },
    {
      title: 'Open Security Cases',
      value: metrics?.open_cases_count ?? 0,
      icon: FolderKanban,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10 border-purple-500/20',
      subtitle: 'SOC Automated Tracking',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl border ${card.bgColor} backdrop-blur-sm transition-all hover:translate-y-[-2px] hover:shadow-lg`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-400">{card.title}</span>
              <Icon className={`w-5 h-5 ${card.color} ${card.alert ? 'animate-bounce' : ''}`} />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">{card.value}</div>
            <p className="text-[11px] text-slate-400 mt-1 truncate">{card.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
};
