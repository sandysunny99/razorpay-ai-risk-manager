import React, { useState, useEffect } from 'react';
import { ShieldAlert, Activity, ChevronRight, ChevronLeft, Radio, ExternalLink } from 'lucide-react';
import { tokens } from '../tokens';

export interface ThreatFeedItem {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MED' | 'LOW';
  timestamp: string;
  description: string;
  cardId?: string;
  source?: string;
}

interface ThreatFeedPanelProps {
  items?: ThreatFeedItem[];
  onSelectCard?: (cardId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const DEFAULT_FEED_ITEMS: ThreatFeedItem[] = [
  {
    id: 'TF-001',
    severity: 'CRITICAL',
    timestamp: 'Just now',
    description: 'Dark-Web Stealer Dump: Token tok_test_8829 matched RedLine Telegram dump',
    cardId: 'card_test_4921',
    source: 'Telegram/RedLine',
  },
  {
    id: 'TF-002',
    severity: 'HIGH',
    timestamp: '2m ago',
    description: 'Geo-Velocity Anomaly: Moscow login 12m after Bengaluru checkout',
    cardId: 'card_test_4921',
    source: 'Cloudflare Edge',
  },
  {
    id: 'TF-003',
    severity: 'MED',
    timestamp: '5m ago',
    description: 'Bot Heuristic: Abnormal header entropy detected on /checkout',
    cardId: 'card_test_1001',
    source: 'WAF Bot-Score 12',
  },
  {
    id: 'TF-004',
    severity: 'CRITICAL',
    timestamp: '8m ago',
    description: 'Zombie Token Detected: Active token on EXPIRED card (4532...1102)',
    cardId: 'card_test_3002',
    source: 'Zombie Vault Watcher',
  },
  {
    id: 'TF-005',
    severity: 'LOW',
    timestamp: '12m ago',
    description: 'Standard domestic card checkout verified (₹2,400.00)',
    cardId: 'card_test_1001',
    source: 'Gateway Telemetry',
  },
];

export const ThreatFeedPanel: React.FC<ThreatFeedPanelProps> = ({
  items = DEFAULT_FEED_ITEMS,
  onSelectCard,
  isOpen,
  onToggle,
}) => {
  const [feed, setFeed] = useState<ThreatFeedItem[]>(items);

  useEffect(() => {
    if (items && items.length > 0) {
      setFeed(items);
    }
  }, [items]);

  // Periodic cycle simulation for SOC real-time atmosphere
  useEffect(() => {
    const timer = setInterval(() => {
      setFeed((prev) => {
        if (prev.length <= 1) return prev;
        const [first, ...rest] = prev;
        return [...rest, { ...first, timestamp: 'Just now' }];
      });
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const getSeverityStyle = (sev: ThreatFeedItem['severity']) => {
    switch (sev) {
      case 'CRITICAL':
        return tokens.threatLevels.critical;
      case 'HIGH':
        return tokens.threatLevels.high;
      case 'MED':
        return tokens.threatLevels.medium;
      case 'LOW':
        return tokens.threatLevels.low;
    }
  };

  return (
    <>
      {/* Floating trigger button when collapsed */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed left-0 top-32 z-40 bg-slate-900/90 text-slate-300 border border-slate-700/80 px-2 py-3 rounded-r-xl shadow-xl hover:bg-slate-800 hover:text-white transition flex flex-col items-center gap-2 group backdrop-blur-md"
          title="Open Live Threat Intelligence Feed"
        >
          <Radio className="w-4 h-4 text-rose-400 animate-pulse" />
          <span className="text-[10px] font-mono [writing-mode:vertical-lr] tracking-widest uppercase font-semibold text-slate-400 group-hover:text-white">
            Threat Feed
          </span>
          <ChevronRight className="w-3 h-3 text-slate-500" />
        </button>
      )}

      {/* Slide-out Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-[280px] bg-[#070F1C]/95 border-r border-slate-800/90 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out backdrop-blur-xl flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-rose-400 animate-pulse" />
            <h3 className="text-xs font-bold font-mono tracking-wider text-white uppercase">
              Live Threat Feed
            </h3>
          </div>
          <button
            onClick={onToggle}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Live status sub-bar */}
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/50 flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            STREAMING (SSE/CTI)
          </span>
          <span>{feed.length} Active Events</span>
        </div>

        {/* Scrollable feed items */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 scrollbar-thin scrollbar-thumb-slate-800">
          {feed.map((item) => {
            const style = getSeverityStyle(item.severity);
            return (
              <div
                key={item.id}
                onClick={() => item.cardId && onSelectCard && onSelectCard(item.cardId)}
                className={`p-3 rounded-lg border transition duration-150 cursor-pointer group hover:scale-[1.01] hover:shadow-md ${
                  item.cardId ? 'hover:border-blue-500/50' : ''
                }`}
                style={{
                  backgroundColor: style.bg,
                  borderColor: style.border,
                }}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span
                    className="px-1.5 py-0.5 rounded text-[9px] font-bold font-mono tracking-wider"
                    style={{ color: style.text, border: `1px solid ${style.border}` }}
                  >
                    {item.severity}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{item.timestamp}</span>
                </div>
                <p className="text-[11px] text-slate-200 leading-snug font-sans mb-1.5">
                  {item.description}
                </p>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span className="truncate max-w-[130px]">{item.source}</span>
                  {item.cardId && (
                    <span className="text-blue-400 group-hover:underline flex items-center gap-0.5">
                      Investigate <ExternalLink className="w-2.5 h-2.5" />
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 text-[10px] font-mono text-slate-500 text-center">
          HMAC-SHA-256 Correlated Feed
        </div>
      </aside>
    </>
  );
};
