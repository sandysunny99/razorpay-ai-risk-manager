import React, { useState, useEffect } from 'react';
import { Radio, AlertOctagon, Flame, ShieldCheck, Database, RefreshCw, ExternalLink } from 'lucide-react';
import { api } from '../services/api';

export function CardExposureOverview() {
  const [stats, setStats] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchExposureData = async () => {
    setLoading(true);
    try {
      const [s, ev] = await Promise.all([
        api.getExposureStatistics().catch(() => null),
        api.getExposureEvents().catch(() => [])
      ]);
      setStats(s);
      setEvents(ev);
    } catch (err) {
      console.error('Error loading exposure data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExposureData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Radio className="w-6 h-6 text-rose-500 animate-pulse" />
            <h2 className="text-xl font-bold text-white tracking-wide">Threat Intelligence & Card Exposure Overview</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Zero-Knowledge HMAC-SHA256 Matcher • Stealer Dumps • DarkWeb Breaches • Pastebin Feeds
          </p>
        </div>
        <button
          onClick={fetchExposureData}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Sync Feeds</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Cards Monitored</span>
          <div className="text-2xl font-bold text-white mt-1">{stats?.cards_monitored ?? '--'}</div>
          <span className="text-[11px] text-slate-500">Vault & Active Gateways</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Breach Matches</span>
          <div className="text-2xl font-bold text-rose-400 mt-1">{stats?.cards_exposed ?? '--'}</div>
          <span className="text-[11px] text-rose-400/80">Correlated in Threat Feeds</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Stealer Dumps</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">{stats?.stealer_dump_matches ?? '--'}</div>
          <span className="text-[11px] text-slate-500">High-Confidence Logs</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Paste Leaks</span>
          <div className="text-2xl font-bold text-cyan-400 mt-1">{stats?.paste_leak_matches ?? '--'}</div>
          <span className="text-[11px] text-slate-500">Public/Pastebin Breaches</span>
        </div>
      </div>

      {/* Exposure Feeds Table */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-rose-400" />
            <h3 className="text-sm font-bold text-white">Correlated Breach & Exposure Event Log</h3>
          </div>
          <span className="text-[11px] text-slate-400">Zero Raw PANs Logged</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">HMAC Fingerprint</th>
                <th className="py-2.5 px-3">BIN</th>
                <th className="py-2.5 px-3">Threat Source</th>
                <th className="py-2.5 px-3">Exposure Type</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Leak Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {events.length > 0 ? (
                events.map((ev, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-2 px-3 text-cyan-300 font-semibold">{ev.card_fingerprint}</td>
                    <td className="py-2 px-3 text-slate-300">{ev.bin}</td>
                    <td className="py-2 px-3 text-slate-300">{ev.source_name}</td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 text-[10px] font-bold bg-rose-500/10 text-rose-400 rounded">
                        {ev.exposure_type}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-amber-300 font-semibold">
                      {(ev.confidence_score * 100).toFixed(0)}%
                    </td>
                    <td className="py-2 px-3 text-slate-400">
                      {ev.leak_date ? new Date(ev.leak_date).toLocaleDateString() : 'Recent'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-slate-500">
                    No active card exposure events found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
