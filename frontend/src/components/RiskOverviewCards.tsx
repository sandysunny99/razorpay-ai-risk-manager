import React from 'react';
import CountUp from 'react-countup';
import { CreditCard, KeyRound, Skull, AlertOctagon, ShieldAlert, FolderKanban, ShieldCheck } from 'lucide-react';
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
      borderAccent: 'border-l-blue-500',
      iconColor: 'text-blue-400',
      badgeColor: 'bg-blue-500/10 text-blue-300',
      subtitle: 'HMAC-SHA-256 Fingerprinted',
    },
    {
      title: 'Tokens Monitored',
      value: metrics?.tokens_monitored ?? 0,
      icon: KeyRound,
      borderAccent: 'border-l-indigo-500',
      iconColor: 'text-indigo-400',
      badgeColor: 'bg-indigo-500/10 text-indigo-300',
      subtitle: 'Vault Managed Tokens',
    },
    {
      title: 'Active Zombie Tokens',
      value: metrics?.active_zombie_tokens ?? 0,
      icon: Skull,
      borderAccent: 'border-l-rose-500',
      iconColor: 'text-rose-400',
      badgeColor: 'bg-rose-500/10 text-rose-300',
      subtitle: 'Tokens on Dead Cards',
      alert: (metrics?.active_zombie_tokens ?? 0) > 0,
    },
    {
      title: 'Exposure Events',
      value: metrics?.exposure_events_count ?? 0,
      icon: AlertOctagon,
      borderAccent: 'border-l-amber-500',
      iconColor: 'text-amber-400',
      badgeColor: 'bg-amber-500/10 text-amber-300',
      subtitle: 'Stealer Logs & Paste Matches',
    },
    {
      title: 'Critical Incidents',
      value: metrics?.critical_incidents ?? 0,
      icon: ShieldAlert,
      borderAccent: 'border-l-red-500',
      iconColor: 'text-red-400',
      badgeColor: 'bg-red-500/10 text-red-300',
      subtitle: 'Immediate Remediation Tier',
    },
    {
      title: 'Open Security Cases',
      value: metrics?.open_cases_count ?? 0,
      icon: FolderKanban,
      borderAccent: 'border-l-purple-500',
      iconColor: 'text-purple-400',
      badgeColor: 'bg-purple-500/10 text-purple-300',
      subtitle: 'Automated SOC Tracking',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl border border-slate-800/80 border-l-4 ${card.borderAccent} bg-slate-900/60 backdrop-blur-md transition-all duration-200 hover:translate-y-[-2px] hover:shadow-lg hover:border-slate-700`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                {card.title}
              </span>
              <Icon className={`w-4 h-4 ${card.iconColor} ${card.alert ? 'animate-pulse' : ''}`} />
            </div>
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              <CountUp end={card.value} duration={0.8} />
            </div>
            <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
              <span className="truncate">{card.subtitle}</span>
              {card.alert && (
                <span className="flex-shrink-0 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  CRITICAL
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
