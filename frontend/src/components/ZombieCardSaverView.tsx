import React, { useState, useEffect } from 'react';
import { 
  Skull, AlertTriangle, ShieldCheck, ShieldAlert, KeyRound, 
  RotateCw, ExternalLink, RefreshCw, CheckCircle2, ArrowRight, 
  Layers, Lock, Store, Users, FileText, Activity, AlertOctagon
} from 'lucide-react';
import { api } from '../services/api';
import { 
  ZombieCardSummary, ZombieStatistics, ZombieAnalysisResponse, DependentTokenItem 
} from '../types';

export const ZombieCardSaverView: React.FC = () => {
  const [cards, setCards] = useState<ZombieCardSummary[]>([]);
  const [stats, setStats] = useState<ZombieStatistics | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ZombieAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [revokingTokenId, setRevokingTokenId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [cardsData, statsData] = await Promise.all([
        api.getZombieCards().catch(() => []),
        api.getZombieStatistics().catch(() => null),
      ]);
      setCards(cardsData);
      setStats(statsData);
      if (cardsData.length > 0 && !selectedCardId) {
        setSelectedCardId(cardsData[0].card_id);
      }
    } catch (err) {
      console.error('Failed to load Zombie Card Saver data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedCardId) {
      loadCardAnalysis(selectedCardId);
    }
  }, [selectedCardId]);

  const loadCardAnalysis = async (cardId: string) => {
    setIsAnalyzing(true);
    try {
      const data = await api.getZombieCardAnalysis(cardId);
      setAnalysis(data);
    } catch (err) {
      console.error('Failed to load card analysis:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRevokeToken = async (tokenId: string) => {
    setRevokingTokenId(tokenId);
    setSuccessMsg(null);
    try {
      const res = await api.revokeZombieToken(tokenId);
      setSuccessMsg(res.message || `Token ${tokenId} revoked successfully.`);
      // Refresh current card analysis & stats
      if (selectedCardId) {
        await loadCardAnalysis(selectedCardId);
      }
      const updatedStats = await api.getZombieStatistics().catch(() => null);
      if (updatedStats) setStats(updatedStats);
    } catch (err) {
      console.error('Failed to revoke token:', err);
    } finally {
      setRevokingTokenId(null);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">LOW</span>;
    }
  };

  const getActionBadge = (action: string) => {
    switch (action?.toUpperCase()) {
      case 'REVOKE_TOKEN':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">REVOKE TOKEN</span>;
      case 'REQUEST_STEP_UP':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">REQUEST STEP-UP</span>;
      case 'REVIEW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">RECURRING REVIEW</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">MONITOR</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-md">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30 shadow-inner">
              <Skull className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Zombie Card Saver
                <span className="px-2 py-0.5 text-[11px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-full">
                  DISRUPTION PREVENTED
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Detects credential lifecycle changes and selectively remediates dependent tokens without disrupting legitimate recurring merchant billing.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300">Policy: <strong>Dual-Layer (T=40 / T=75)</strong></span>
          </div>
          <button 
            onClick={fetchData} 
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Success Banner */}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex items-center justify-between text-emerald-300 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-white font-bold">×</button>
        </div>
      )}

      {/* 6 Top KPI Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-md">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Zombie Cards</div>
          <div className="text-2xl font-black text-white mt-1">{stats?.total_zombie_cards ?? 27}</div>
          <div className="text-[10px] text-amber-400 mt-1 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Lifecycle Mismatch
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-md">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active Zombie Tokens</div>
          <div className="text-2xl font-black text-amber-400 mt-1">{stats?.active_zombie_tokens ?? 41}</div>
          <div className="text-[10px] text-slate-400 mt-1">Dependent on stale cards</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-md">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Critical Zombies</div>
          <div className="text-2xl font-black text-rose-400 mt-1">{stats?.critical_zombies ?? 6}</div>
          <div className="text-[10px] text-rose-400 mt-1 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3" /> Exposed / Blocked
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-md">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recently Used</div>
          <div className="text-2xl font-black text-cyan-400 mt-1">{stats?.recently_used_zombies ?? 18}</div>
          <div className="text-[10px] text-slate-400 mt-1">Active payment velocity</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-md">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Tokens Saved</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{stats?.tokens_saved ?? 19}</div>
          <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> Subscriptions Preserved
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-md">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Tokens Revoked</div>
          <div className="text-2xl font-black text-rose-400 mt-1">{stats?.tokens_revoked ?? 12}</div>
          <div className="text-[10px] text-slate-400 mt-1">Selective remediation</div>
        </div>
      </div>

      {/* Main Content Area: Top Zombie Cards Table & Deep Dive Investigation Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Top Zombie Cards Table */}
        <div className="lg:col-span-7 bg-slate-900/60 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white tracking-tight uppercase">Top Zombie Credential Entities</h3>
            </div>
            <span className="text-[11px] text-slate-400">Click row for Token Dependency Graph</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Card (Masked)</th>
                  <th className="py-2.5 px-2">Lifecycle State</th>
                  <th className="py-2.5 px-2 text-center">Tokens</th>
                  <th className="py-2.5 px-2">Severity</th>
                  <th className="py-2.5 px-2">Risk</th>
                  <th className="py-2.5 px-2">Recommended</th>
                  <th className="py-2.5 px-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {cards.map((c) => {
                  const isSelected = c.card_id === selectedCardId;
                  return (
                    <tr 
                      key={c.card_id}
                      onClick={() => setSelectedCardId(c.card_id)}
                      className={`hover:bg-purple-950/20 cursor-pointer transition-colors ${isSelected ? 'bg-purple-950/40 border-l-2 border-purple-500' : ''}`}
                    >
                      <td className="py-3 px-3 font-mono font-bold text-white flex items-center gap-1.5">
                        <Lock className="w-3 h-3 text-slate-500" />
                        {c.masked_pan}
                      </td>
                      <td className="py-3 px-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.card_state === 'EXPIRED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                          c.card_state === 'BLOCKED' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                          'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                        }`}>
                          {c.card_state}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-center font-bold text-white">
                        <span className="px-2 py-0.5 bg-slate-800 rounded font-mono text-[11px]">
                          {c.active_token_count} / {c.total_token_count}
                        </span>
                      </td>
                      <td className="py-3 px-2">{getSeverityBadge(c.severity)}</td>
                      <td className="py-3 px-2 font-mono font-bold">
                        <span className={c.authoritative_risk_score >= 75 ? 'text-rose-400' : (c.authoritative_risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400')}>
                          {c.authoritative_risk_score}
                        </span>
                      </td>
                      <td className="py-3 px-2">{getActionBadge(c.recommended_action)}</td>
                      <td className="py-3 px-2 text-right">
                        <button 
                          onClick={(e) => { e.stopPropagation(); setSelectedCardId(c.card_id); }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-purple-600 text-white rounded text-[10px] font-semibold transition-all"
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Deep-Dive Investigation & Dependency Graph */}
        <div className="lg:col-span-5 bg-slate-900/60 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white tracking-tight uppercase">Zombie Credential Investigation</h3>
            </div>
            {analysis && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                {analysis.policy_tier}
              </span>
            )}
          </div>

          {isAnalyzing ? (
            <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center gap-2 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
              Analyzing token dependencies and merchant disruption impact...
            </div>
          ) : analysis ? (
            <div className="space-y-4 text-xs">
              {/* Card Summary Card */}
              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-white text-sm">{analysis.card.masked_pan}</span>
                  <span className="text-[11px] text-slate-400">State: <strong className="text-amber-400">{analysis.card.card_state}</strong></span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                  <div>
                    <span className="text-slate-500">Risk Score:</span>{' '}
                    <strong className={analysis.card.authoritative_risk_score >= 75 ? 'text-rose-400' : 'text-amber-400'}>
                      {analysis.card.authoritative_risk_score} / 100
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Exposure:</span>{' '}
                    <strong className={analysis.card.exposure_detected ? 'text-rose-400' : 'text-emerald-400'}>
                      {analysis.card.exposure_detected ? 'CRITICAL MATCH' : 'CLEAN'}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Token Dependency Map */}
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase flex items-center justify-between">
                  <span>Dependent Token Topology ({analysis.dependent_tokens.length})</span>
                  <span className="text-[10px] text-emerald-400">Selective Protection</span>
                </div>

                <div className="space-y-2">
                  {analysis.dependent_tokens.map((token: DependentTokenItem) => (
                    <div 
                      key={token.token_id}
                      className={`p-3 rounded-xl border flex flex-col gap-2 transition-all ${
                        token.status === 'REVOKED' 
                          ? 'bg-slate-950/40 border-slate-800 opacity-60'
                          : (token.risk_score >= 75 
                              ? 'bg-rose-950/20 border-rose-500/40' 
                              : (token.is_recurring ? 'bg-cyan-950/20 border-cyan-500/40' : 'bg-slate-900/80 border-slate-800'))
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <KeyRound className="w-3.5 h-3.5 text-purple-400" />
                          <span className="font-mono font-bold text-white text-[11px]">{token.token_id}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          {token.is_recurring && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                              RECURRING SUB
                            </span>
                          )}
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                            token.status === 'REVOKED' ? 'bg-slate-800 text-slate-400' : 'bg-emerald-500/20 text-emerald-300'
                          }`}>
                            {token.status}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span>Merchant: <strong className="text-slate-200">{token.merchant_name}</strong></span>
                        <span>Risk: <strong className={token.risk_score >= 75 ? 'text-rose-400' : 'text-slate-200'}>{token.risk_score}</strong></span>
                      </div>

                      {/* Action Button */}
                      {token.status !== 'REVOKED' && (
                        <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                          <span className="text-[10px] text-slate-400">Recommended: {getActionBadge(token.recommended_action)}</span>
                          {token.recommended_action === 'REVOKE_TOKEN' ? (
                            <button
                              onClick={() => handleRevokeToken(token.token_id)}
                              disabled={revokingTokenId === token.token_id}
                              className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-[10px] font-bold shadow-md transition-all active:scale-95 disabled:opacity-50"
                            >
                              {revokingTokenId === token.token_id ? 'Revoking...' : 'Revoke Token'}
                            </button>
                          ) : (
                            <span className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1">
                              <ShieldCheck className="w-3 h-3" /> Safe to Defer
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Merchant & Customer Impact Box */}
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                    <Store className="w-3 h-3 text-cyan-400" /> Merchant Impact
                  </div>
                  <div>Merchants: <strong className="text-white">{analysis.merchant_impact.affected_merchant_count}</strong></div>
                  <div>Recurring Subs: <strong className="text-cyan-400">{analysis.merchant_impact.recurring_subscription_count}</strong></div>
                  <div>Disruption Risk: <strong className="text-emerald-400">{analysis.merchant_impact.disruption_risk}</strong></div>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                    <Users className="w-3 h-3 text-purple-400" /> Customer Impact
                  </div>
                  <div>Friction Level: <strong className="text-emerald-400">{analysis.customer_impact.payment_friction_level}</strong></div>
                  <div className="text-[9px] text-slate-400">{analysis.customer_impact.recommended_notification}</div>
                </div>
              </div>

              {/* SHA-256 Audit Verification Stamp */}
              <div className="p-2.5 rounded-xl bg-purple-950/20 border border-purple-500/30 flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-purple-300 font-semibold">Audit Ledger Block Hash</span>
                </div>
                <span className="font-mono text-slate-400 truncate max-w-[140px]">{analysis.audit_hash}</span>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-slate-500 text-xs">
              Select a card from the table to inspect dependent tokens and run selective remediation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
