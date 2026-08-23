import React from 'react';
import { Skull, AlertTriangle, ShieldAlert, KeyRound, Check } from 'lucide-react';
import { ZombieTokenAlert } from '../types';

interface ZombieTokenAlertsProps {
  zombies: ZombieTokenAlert[];
  onRevoke: (tokenId: string) => void;
  isRevoking?: string | null;
}

export const ZombieTokenAlerts: React.FC<ZombieTokenAlertsProps> = ({
  zombies,
  onRevoke,
  isRevoking,
}) => {
  if (!zombies || zombies.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Check className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Zombie Token Vault Healthy</div>
            <div className="text-[11px] text-slate-400">Zero active tokens detected on expired or blocked cards</div>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          0 DETECTED
        </span>
      </div>
    );
  }

  return (
    <div className="bg-[#181528] border border-rose-500/40 rounded-2xl p-5 shadow-xl space-y-3 relative overflow-hidden">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skull className="w-5 h-5 text-rose-400 animate-pulse" />
          <h3 className="text-sm font-bold text-rose-300 tracking-tight">
            CRITICAL ZOMBIE TOKEN DETECTIONS ({zombies.length})
          </h3>
        </div>
        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
          IMMEDIATE REMEDIATION REQUIRED
        </span>
      </div>
      <p className="text-xs text-slate-300">
        The following payment tokens remain <span className="text-rose-400 font-semibold">ACTIVE</span> on gateway vaults despite their parent credit cards being expired or blocked.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
        {zombies.map((z) => (
          <div
            key={z.token_id}
            className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-500/30 flex flex-col justify-between gap-3 shadow-inner"
          >
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-white font-mono">{z.token_id}</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                  {z.risk_level}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 space-y-0.5">
                <div>Parent Card: <span className="font-mono text-slate-200">{z.masked_pan}</span> ({z.card_status})</div>
                <div>Card Expired: <span className="text-rose-400 font-semibold">{z.is_card_expired ? 'YES' : 'NO'}</span></div>
                <div>Last Token Usage: <span className="text-slate-300">{new Date(z.last_used).toLocaleString()}</span></div>
              </div>
              <p className="text-[11px] text-rose-300/90 mt-2 bg-rose-950/30 p-2 rounded border border-rose-900/50 leading-relaxed">
                {z.reason}
              </p>
            </div>

            <button
              onClick={() => onRevoke(z.token_id)}
              disabled={isRevoking === z.token_id}
              className="w-full py-2 px-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow transition disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {isRevoking === z.token_id ? (
                <span>Revoking Token...</span>
              ) : (
                <>
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>Autonomous Policy Revoke</span>
                </>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
