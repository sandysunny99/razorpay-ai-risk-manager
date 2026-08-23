import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { RiskOverviewCards } from './components/RiskOverviewCards';
import { DemoScenarioTrigger } from './components/DemoScenarioTrigger';
import { InvestigationTimeline } from './components/InvestigationTimeline';
import { ZombieTokenAlerts } from './components/ZombieTokenAlerts';
import { CardRiskTable } from './components/CardRiskTable';
import { SecurityCasesTable } from './components/SecurityCasesTable';
import { AuditTrailTable } from './components/AuditTrailTable';
import { EvaluationDashboard } from './components/EvaluationDashboard';
import { LiveRiskTable } from './components/LiveRiskTable';

import { api } from './services/api';
import {
  OverviewMetrics,
  InvestigationResponse,
  CardItem,
  TokenItem,
  ZombieTokenAlert,
  SecurityCase,
  AuditEvent,
  ScenarioItem,
} from './types';

export function App() {
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [cards, setCards] = useState<CardItem[]>([]);
  const [tokens, setTokens] = useState<TokenItem[]>([]);
  const [zombies, setZombies] = useState<ZombieTokenAlert[]>([]);
  const [cases, setCases] = useState<SecurityCase[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  
  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAgentRunning, setIsAgentRunning] = useState<boolean>(false);
  const [revokingTokenId, setRevokingTokenId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'evaluation' | 'liverisk' | 'cards' | 'cases' | 'audit'>('timeline');

  const fetchAllData = async () => {
    setIsLoading(true);
    try {
      const [m, c, t, z, cs, a, sc] = await Promise.all([
        api.getOverview().catch(() => null),
        api.getCards().catch(() => []),
        api.getTokens().catch(() => []),
        api.getZombieTokens().catch(() => []),
        api.getCases().catch(() => []),
        api.getAuditEvents().catch(() => []),
        api.getScenarios().catch(() => []),
      ]);

      if (m) setMetrics(m);
      setCards(c);
      setTokens(t);
      setZombies(z);
      setCases(cs);
      setAuditEvents(a);
      setScenarios(sc);
    } catch (err) {
      console.error('Error refreshing data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleTriggerScenario = async (scenarioId: string) => {
    setIsAgentRunning(true);
    try {
      if (scenarioId === 'golden_compromise') {
        const result = await api.triggerGoldenDemo();
        setInvestigation(result);
        setActiveTab('timeline');
      } else if (scenarioId === 'policy_denial') {
        const result = await api.triggerPolicyDenialDemo();
        alert(`Guardrail Test Result:\n\nAction: ${result.action_requested}\nDecision: ${result.policy_decision.decision}\nReason: ${result.policy_decision.reason}\n\nGuardrail Enforced: ${result.guardrail_enforced}`);
      } else if (scenarioId === 'prompt_injection') {
        const result = await api.triggerPromptInjectionDemo();
        alert(`Prompt Injection Defense Test:\n\nRaw Payload: ${result.raw_payload}\n\nSanitized: ${result.sanitized_payload}\n\nIsolation: ${result.data_isolation}\n\nStatus: ${result.defense_status}`);
      } else if (scenarioId === 'clean_transaction') {
        const result = await api.triggerInvestigation('TXN-2026-1001');
        setInvestigation(result);
        setActiveTab('timeline');
      } else if (scenarioId === 'zombie_token_scan') {
        await fetchAllData();
        setActiveTab('cards');
      }
      await fetchAllData();
    } catch (err) {
      console.error('Scenario execution failed:', err);
    } finally {
      setIsAgentRunning(false);
    }
  };

  const handleResetData = async () => {
    setIsLoading(true);
    try {
      await api.resetData();
      setInvestigation(null);
      await fetchAllData();
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevokeToken = async (tokenId: string) => {
    setRevokingTokenId(tokenId);
    try {
      await api.revokeToken(tokenId);
      await fetchAllData();
    } catch (err) {
      console.error('Revoke failed:', err);
    } finally {
      setRevokingTokenId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#081220] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Header */}
      <Header
        onRefresh={fetchAllData}
        isLoading={isLoading}
        systemStatus={metrics?.system_status || 'OPERATIONAL'}
        dryRun={metrics?.dry_run_mode ?? true}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Executive Metric Cards */}
        <RiskOverviewCards metrics={metrics} />

        {/* Demo Scenario Controller */}
        <DemoScenarioTrigger
          onTriggerScenario={handleTriggerScenario}
          onResetData={handleResetData}
          scenarios={scenarios}
          isRunning={isAgentRunning}
        />

        {/* Zombie Token Alert Section */}
        <ZombieTokenAlerts
          zombies={zombies}
          onRevoke={handleRevokeToken}
          isRevoking={revokingTokenId}
        />

        {/* Tab Navigation */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
              activeTab === 'timeline'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Agent Investigation Timeline {investigation && '• Active'}
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
              activeTab === 'evaluation'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Model Evaluation & Metrics (Held-Out Test Set)
          </button>
          <button
            onClick={() => setActiveTab('liverisk')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
              activeTab === 'liverisk'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Live Risk Screening Stream
          </button>
          <button
            onClick={() => setActiveTab('cards')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
              activeTab === 'cards'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Cards & Vault Inventory ({cards.length})
          </button>
          <button
            onClick={() => setActiveTab('cases')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
              activeTab === 'cases'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Security Cases ({cases.length})
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
              activeTab === 'audit'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            Tamper-Evident Audit Trail ({auditEvents.length})
          </button>
        </div>

        {/* Tab Content Panes */}
        {activeTab === 'timeline' && (
          <InvestigationTimeline investigation={investigation} />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationDashboard />
        )}

        {activeTab === 'liverisk' && (
          <LiveRiskTable
            onInvestigateTransaction={() => handleTriggerScenario('golden_compromise')}
            isInvestigating={isAgentRunning}
          />
        )}

        {activeTab === 'cards' && (
          <CardRiskTable
            cards={cards}
            onInvestigateCard={() => handleTriggerScenario('golden_compromise')}
            isInvestigating={isAgentRunning}
          />
        )}

        {activeTab === 'cases' && (
          <SecurityCasesTable cases={cases} />
        )}

        {activeTab === 'audit' && (
          <AuditTrailTable events={auditEvents} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#060D17] py-6 px-6 text-center text-xs text-slate-500">
        <p>
          Razorpay AI Buildathon 2026 • Track: <span className="text-slate-300 font-medium">AI Risk Manager</span> • Built with HMAC-SHA-256 PAN Fingerprinting & PCI-Aware Security Design
        </p>
      </footer>
    </div>
  );
}

export default App;
