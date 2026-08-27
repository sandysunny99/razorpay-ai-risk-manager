import React from 'react';
import { Keyboard, X } from 'lucide-react';

interface ShortcutsHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsHelpModal: React.FC<ShortcutsHelpModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const shortcuts = [
    { key: '⌘K / Ctrl+K', desc: 'Open Command Palette (search cards, alerts, scenarios)' },
    { key: '⌘D / Ctrl+D', desc: 'Launch Golden Compromise Attack Scenario' },
    { key: '⌘R / Ctrl+R', desc: 'Reset Demo Environment and Seed Data' },
    { key: '1, 2, 3, 4', desc: 'Switch Between Top SOC Dashboard Tabs' },
    { key: '?', desc: 'Toggle this Keyboard Shortcuts Reference' },
    { key: 'Escape', desc: 'Dismiss Active Modal or Command Palette' },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-[#091526] border border-slate-700/80 rounded-2xl shadow-2xl p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Keyboard className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">SOC TERMINAL KEYBOARD SHORTCUTS</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-2.5">
          {shortcuts.map((s, idx) => (
            <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <span className="text-xs text-slate-300">{s.desc}</span>
              <kbd className="px-2 py-1 rounded bg-slate-800 border border-slate-700 font-mono text-[10px] font-bold text-blue-300 whitespace-nowrap">
                {s.key}
              </kbd>
            </div>
          ))}
        </div>

        <div className="pt-2 text-center">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white rounded-lg transition"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
