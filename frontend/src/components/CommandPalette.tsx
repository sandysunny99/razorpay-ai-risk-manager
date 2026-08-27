import React, { useState, useEffect, useRef } from 'react';
import { Search, CreditCard, ShieldAlert, Play, History, X, ArrowRight } from 'lucide-react';
import { CardItem, ScenarioItem, AuditEvent, ZombieTokenAlert } from '../types';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  cards: CardItem[];
  scenarios: ScenarioItem[];
  zombies: ZombieTokenAlert[];
  auditEvents: AuditEvent[];
  onSelectCard: (cardId: string) => void;
  onSelectScenario: (scenarioId: string) => void;
}

interface PaletteItem {
  id: string;
  category: 'Card' | 'Scenario' | 'Zombie Alert' | 'Audit';
  title: string;
  subtitle: string;
  icon: any;
  action: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  cards,
  scenarios,
  zombies,
  auditEvents,
  onSelectCard,
  onSelectScenario,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Build searchable items
  const items: PaletteItem[] = [
    ...scenarios.map((s) => ({
      id: `scen_${s.id}`,
      category: 'Scenario' as const,
      title: s.name,
      subtitle: s.description,
      icon: Play,
      action: () => {
        onSelectScenario(s.id);
        onClose();
      },
    })),
    ...cards.map((c) => ({
      id: `card_${c.card_id}`,
      category: 'Card' as const,
      title: `${c.cardholder_name} (${c.masked_pan})`,
      subtitle: `Status: ${c.status} • Risk: ${c.previous_fraud_count > 0 ? 'HIGH' : 'NORMAL'}`,
      icon: CreditCard,
      action: () => {
        onSelectCard(c.card_id);
        onClose();
      },
    })),
    ...zombies.map((z) => ({
      id: `zomb_${z.token_id}`,
      category: 'Zombie Alert' as const,
      title: `Dead Card Token: ${z.token_id}`,
      subtitle: `Masked: ${z.masked_pan || '****'} • Card Status: ${z.card_status || 'EXPIRED'} • ${z.reason || 'Active token on dead card'}`,
      icon: ShieldAlert,
      action: () => {
        onSelectCard(z.card_id);
        onClose();
      },
    })),
    ...auditEvents.slice(0, 10).map((a) => ({
      id: `aud_${a.event_id}`,
      category: 'Audit' as const,
      title: `${a.event_id} - ${a.action_executed || 'MONITOR'}`,
      subtitle: `Score: ${a.risk_score} • Policy: ${a.policy_evaluated}`,
      icon: History,
      action: () => {
        onClose();
      },
    })),
  ];

  const filtered = query.trim()
    ? items.filter(
        (i) =>
          i.title.toLowerCase().includes(query.toLowerCase()) ||
          i.subtitle.toLowerCase().includes(query.toLowerCase()) ||
          i.category.toLowerCase().includes(query.toLowerCase())
      )
    : items.slice(0, 8);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/75 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-[#091526] border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3">
          <Search className="w-5 h-5 text-blue-400 flex-shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Search cards, scenarios, alerts, audit IDs..."
            className="w-full bg-transparent text-sm text-white placeholder-slate-400 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results list */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1 scrollbar-thin">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No matching records found for "{query}".
            </div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`p-3 rounded-xl flex items-center justify-between cursor-pointer transition ${
                    isSelected
                      ? 'bg-blue-600/20 border border-blue-500/40 text-white'
                      : 'hover:bg-slate-800/50 text-slate-300 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={`p-2 rounded-lg ${
                        isSelected ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold truncate">{item.title}</span>
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-slate-800 text-slate-400 border border-slate-700">
                          {item.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">{item.subtitle}</p>
                    </div>
                  </div>
                  <ArrowRight
                    className={`w-4 h-4 flex-shrink-0 transition ${
                      isSelected ? 'text-blue-400 translate-x-1' : 'text-slate-600'
                    }`}
                  />
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts hint */}
        <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
          <span>↑↓ to navigate • ↵ to select</span>
          <span>ESC to exit</span>
        </div>
      </div>
    </div>
  );
};
