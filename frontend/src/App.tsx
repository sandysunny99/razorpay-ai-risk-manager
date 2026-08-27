import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { RiskOverviewCards } from './components/RiskOverviewCards';
import { DemoScenarioTrigger } from './components/DemoScenarioTrigger';
import { InvestigationTimeline } from './components/InvestigationTimeline';
import { CardRiskTable } from './components/CardRiskTable';
import { SecurityCasesTable } from './components/SecurityCasesTable';
import { AuditTrailTable } from './components/AuditTrailTable';
import { EvaluationDashboard } from './components/EvaluationDashboard';
import { LiveRiskTable } from './components/LiveRiskTable';
import { ZombieCardSaverView } from './components/ZombieCardSaverView';
import { SecurityCenter } from './components/SecurityCenter';
import { CardExposureOverview } from './components/CardExposureOverview';
import { ThreatFeedPanel } from './components/ThreatFeedPanel';
import { CommandPalette } from './components/CommandPalette';
import { ShortcutsHelpModal } from './components/ShortcutsHelpModal';
import { RiskHeatmap } from './components/RiskHeatmap';
import { ToastContainer } from './components/ToastContainer';
import { TableSkeleton } from './components/Skeleton';
import { useToast } from './hooks/useToast';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { api, setApiErrorListener } from './services/api';
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

type TabType =
  | 'timeline'
  | 'heatmap'
  | 'zombie-saver'
  | 'evaluation'
  | 'liverisk'
  | 'cards'
  | 'cases'
  | 'audit'
  | 'security'
  | 'exposure';

export function App() {
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [cards, setCards] = useState<CardItem[]>([]);
  const [, setTokens] = useState<TokenItem[]>([]);
  const [zombies, setZombies] = useState<ZombieTokenAlert[]>([]);
  const [cases, setCases] = useState<SecurityCase[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);

  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAgentRunning, setIsAgentRunning] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<TabType>('timeline');

  // Interactive SOC overlays
  const [isThreatFeedOpen, setIsThreatFeedOpen] = useState<boolean>(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);
  const [isShortcutsHelpOpen, setIsShortcutsHelpOpen] = useState<boolean>(false);

  const { toasts, addToast, dismissToast } = useToast();

  // Wire API global error handler to toast system (BUG-UI-05)
  useEffect(() => {
    setApiErrorListener((msg: string) => {
      addToast({
        type: 'error',
        title: 'Backend Communication Alert',
        message: msg,
      });
    });
    return () => setApiErrorListener(null);
  }, [addToast]);

  const fetchAllData = useCallback(async () => {
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
    } catch (err: any) {
      console.error('Error refreshing data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  const handleTriggerScenario = async (scenarioId: string) => {
    setIsAgentRunning(true);
    try {
      if (scenarioId === 'golden_compromise') {
        const result = await api.triggerGoldenDemo();
        setInvestigation(result);
        setActiveTab('timeline');
        addToast({
          type: 'security',
          title: 'Golden Compromise Scenario Executed',
          message: `Autonomous mitigation complete: Risk ${result.initial_risk} -> ${result.final_risk}. Token revoked.`,
        });
      } else if (scenarioId === 'policy_denial') {
        const result = await api.triggerPolicyDenialDemo();
        addToast({
          type: 'security',
          title: 'Policy Guardrail Enforced (PG-CARD-01)',
          message: `Blocked Action: ${result.action_requested} | Decision: ${result.policy_decision?.decision || 'BLOCKED'} | Reason: Supervisor review strictly required.`,
        });
      } else if (scenarioId === 'prompt_injection') {
        const result = await api.triggerPromptInjectionDemo();
        addToast({
          type: 'success',
          title: 'Adversarial Prompt Injection Defended',
          message: `Threat text neutralized. Status: ${result.defense_status} | Isolation: Strict schema separation verified.`,
        });
      } else if (scenarioId === 'clean_transaction') {
        const result = await api.triggerInvestigation('TXN-2026-1001');
        setInvestigation(result);
        setActiveTab('timeline');
        addToast({
          type: 'info',
          title: 'Clean Domestic Benchmark Evaluated',
          message: `Risk Score: ${result.initial_risk}/100. Policy: ALLOW. No remediation required.`,
        });
      } else if (scenarioId === 'zombie_token_scan') {
        await fetchAllData();
        setActiveTab('zombie-saver');
        addToast({
          type: 'warning',
          title: 'Zombie Token Scan Completed',
          message: `Found active vault tokens bound to expired/blocked cards.`,
        });
      }
      await fetchAllData();
    } catch (err: any) {
      console.error('Scenario execution failed:', err);
    } finally {
      setIsAgentRunning(false);
    }
  };

  const handleInvestigateCard = async (cardId: string) => {
    setIsAgentRunning(true);
    try {
      const card = cards.find((c) => c.card_id === cardId);
      const targetTxn =
        cardId === 'card_test_4921' || card?.masked_pan?.includes('4921')
          ? 'TXN-2026-9042'
          : 'TXN-2026-1001';
      const result = await api.triggerInvestigation(targetTxn);
      setInvestigation(result);
      setActiveTab('timeline');
      addToast({
        type: 'info',
        title: 'Targeted Card Investigation',
        message: `Analyzing risk timeline for card ${card?.masked_pan || cardId} via transaction ${targetTxn}.`,
      });
    } catch (err: any) {
      console.error('Investigation failed:', err);
    } finally {
      setIsAgentRunning(false);
    }
  };

  const handleInvestigateTxn = async (txnId: string) => {
    setIsAgentRunning(true);
    try {
      const result = await api.triggerInvestigation(txnId);
      setInvestigation(result);
      setActiveTab('timeline');
      addToast({
        type: 'info',
        title: 'Transaction Investigation',
        message: `Evaluating multi-factor risk for ${txnId}.`,
      });
    } catch (err: any) {
      console.error('Investigation failed:', err);
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
      addToast({
        type: 'success',
        title: 'Demo Environment Reset',
        message: 'Database reseeded with initial deterministic fixtures.',
      });
    } catch (err: any) {
      console.error('Reset failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs: { id: TabType; label: string; count?: number; isLive?: boolean }[] = [
    { id: 'timeline', label: 'Forensic Timeline', count: investigation ? 1 : undefined },
    { id: 'heatmap', label: 'Risk Heatmap Matrix' },
    { id: 'zombie-saver', label: 'Zombie Card Saver', count: zombies.length },
    { id: 'liverisk', label: 'Risk Screening (Simulation)', isLive: true },
    { id: 'cards', label: 'Cards & Vault', count: cards.length },
    { id: 'cases', label: 'Security Cases', count: cases.length },
    { id: 'audit', label: 'Audit Ledger', count: auditEvents.length },
    { id: 'security', label: 'SOC & DLP Guard' },
    { id: 'exposure', label: 'Threat Intel & CTI' },
    { id: 'evaluation', label: 'Model Evaluation' },
  ];

  // Hotkey handlers (TASK 3E)
  useKeyboardShortcuts({
    onOpenCommandPalette: () => setIsCommandPaletteOpen((prev) => !prev),
    onGoldenDemo: () => handleTriggerScenario('golden_compromise'),
    onResetDemo: handleResetData,
    onCloseModals: () => {
      setIsCommandPaletteOpen(false);
      setIsShortcutsHelpOpen(false);
      setIsThreatFeedOpen(false);
    },
    onSwitchTab: (idx: number) => {
      if (tabs[idx]) setActiveTab(tabs[idx].id);
    },
    onToggleShortcutsHelp: () => setIsShortcutsHelpOpen((prev) => !prev),
  });

  const globalScore = investigation?.initial_risk || 82;

  return (
    <div className="min-h-screen bg-[#081220] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white relative">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Slide-out Threat Feed Panel (TASK 3A) */}
      <ThreatFeedPanel
        isOpen={isThreatFeedOpen}
        onToggle={() => setIsThreatFeedOpen((prev) => !prev)}
        onSelectCard={handleInvestigateCard}
      />

      {/* Centered Command Palette Modal (TASK 3F) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        cards={cards}
        scenarios={scenarios}
        zombies={zombies}
        auditEvents={auditEvents}
        onSelectCard={handleInvestigateCard}
        onSelectScenario={handleTriggerScenario}
      />

      {/* Keyboard Shortcuts Help Modal */}
      <ShortcutsHelpModal
        isOpen={isShortcutsHelpOpen}
        onClose={() => setIsShortcutsHelpOpen(false)}
      />

      {/* Top Header with Global Threat Level Bar (TASK 3D) */}
      <Header
        onRefresh={fetchAllData}
        isLoading={isLoading}
        systemStatus={metrics?.system_status || 'OPERATIONAL'}
        dryRun={metrics?.dry_run_mode ?? true}
        globalThreatScore={globalScore}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenShortcuts={() => setIsShortcutsHelpOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Executive Metric Cards */}
        <RiskOverviewCards metrics={metrics} />

        {/* Demo Scenario Interactive Controller */}
        <DemoScenarioTrigger
          scenarios={scenarios}
          onTriggerScenario={handleTriggerScenario}
          onResetData={handleResetData}
          isRunning={isAgentRunning}
        />

        {/* Pill-Style Tab Navigation */}
        <nav className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-slate-800/80 scrollbar-none">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-150 ${
                  isActive
                    ? 'bg-blue-600/90 text-white shadow-lg shadow-blue-500/25 border border-blue-400/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <span>{tab.label}</span>
                {tab.isLive && (
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                )}
                {tab.count !== undefined && tab.count > 0 && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-800 text-slate-300 border border-slate-700'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Tab Content Panes */}
        {isLoading && !investigation && <TableSkeleton rows={6} />}

        {!isLoading && activeTab === 'timeline' && (
          <InvestigationTimeline investigation={investigation} />
        )}

        {activeTab === 'heatmap' && (
          <RiskHeatmap onSelectTransaction={handleInvestigateTxn} />
        )}

        {activeTab === 'zombie-saver' && <ZombieCardSaverView />}

        {activeTab === 'security' && <SecurityCenter />}

        {activeTab === 'exposure' && <CardExposureOverview />}

        {activeTab === 'evaluation' && <EvaluationDashboard />}

        {activeTab === 'liverisk' && (
          <LiveRiskTable
            onInvestigateTransaction={() => handleTriggerScenario('golden_compromise')}
            isInvestigating={isAgentRunning}
          />
        )}

        {activeTab === 'cards' && (
          <CardRiskTable
            cards={cards}
            onInvestigateCard={handleInvestigateCard}
            isInvestigating={isAgentRunning}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'cases' && <SecurityCasesTable cases={cases} />}

        {activeTab === 'audit' && (
          <AuditTrailTable events={auditEvents} isLoading={isLoading} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#060D17] py-6 px-6 text-center text-xs text-slate-500">
        <p>
          Razorpay AI Buildathon 2026 • Track:{' '}
          <span className="text-slate-300 font-medium">AI Risk Manager</span> • Press{' '}
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[10px] text-blue-300">
            ?
          </kbd>{' '}
          for keyboard shortcuts or{' '}
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[10px] text-blue-300">
            ⌘K
          </kbd>{' '}
          for command palette.
        </p>
      </footer>
    </div>
  );
}

export default App;
