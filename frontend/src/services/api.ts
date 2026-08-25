import {
  OverviewMetrics,
  InvestigationResponse,
  CardItem,
  TokenItem,
  ZombieTokenAlert,
  SecurityCase,
  AuditEvent,
  ScenarioItem,
} from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

export const api = {
  async getOverview(): Promise<OverviewMetrics> {
    const res = await fetch(`${API_BASE}/risk/overview`);
    if (!res.ok) throw new Error('Failed to fetch risk overview');
    return res.json();
  },

  async triggerInvestigation(txnId?: string): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE}/risk/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transaction_id: txnId }),
    });
    if (!res.ok) throw new Error('Investigation request failed');
    return res.json();
  },

  async triggerGoldenDemo(): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE}/demo/trigger-golden-scenario`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Golden scenario trigger failed');
    return res.json();
  },

  async triggerPolicyDenialDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/trigger-policy-denial-scenario`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Policy denial scenario trigger failed');
    return res.json();
  },

  async triggerPromptInjectionDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/trigger-prompt-injection-scenario`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Prompt injection scenario trigger failed');
    return res.json();
  },

  async verifyAuditChain(): Promise<{ valid: boolean; total_events: number; status: string; tampered_events: any[]; head_hash?: string }> {
    const res = await fetch(`${API_BASE}/audit/verify`);
    if (!res.ok) throw new Error('Audit chain verification failed');
    return res.json();
  },

  async getScenarios(): Promise<ScenarioItem[]> {
    const res = await fetch(`${API_BASE}/demo/scenarios`);
    if (!res.ok) throw new Error('Failed to fetch scenarios');
    return res.json();
  },

  async resetData(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/demo/reset-data`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to reset data');
    return res.json();
  },

  async getCards(): Promise<CardItem[]> {
    const res = await fetch(`${API_BASE}/cards`);
    if (!res.ok) throw new Error('Failed to fetch cards');
    return res.json();
  },

  async getTokens(): Promise<TokenItem[]> {
    const res = await fetch(`${API_BASE}/tokens`);
    if (!res.ok) throw new Error('Failed to fetch tokens');
    return res.json();
  },

  async getZombieTokens(): Promise<ZombieTokenAlert[]> {
    const res = await fetch(`${API_BASE}/tokens/zombies`);
    if (!res.ok) throw new Error('Failed to fetch zombie tokens');
    return res.json();
  },

  async revokeToken(tokenId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/tokens/${tokenId}/revoke`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Token revocation failed');
    return res.json();
  },

  async getCases(): Promise<SecurityCase[]> {
    const res = await fetch(`${API_BASE}/cases`);
    if (!res.ok) throw new Error('Failed to fetch cases');
    return res.json();
  },

  async getAuditEvents(): Promise<AuditEvent[]> {
    const res = await fetch(`${API_BASE}/audit/events`);
    if (!res.ok) throw new Error('Failed to fetch audit events');
    return res.json();
  },

  async getEvaluationMetrics(split: string = 'test.jsonl', threshold: number = 75.0): Promise<any> {
    const res = await fetch(`${API_BASE}/evaluation/metrics?split=${split}&threshold=${threshold}`);
    if (!res.ok) throw new Error('Failed to fetch evaluation metrics');
    return res.json();
  },

  async getAblationStudy(split: string = 'test.jsonl'): Promise<any[]> {
    const res = await fetch(`${API_BASE}/evaluation/ablation?split=${split}`);
    if (!res.ok) throw new Error('Failed to fetch ablation study');
    return res.json();
  },

  async getThresholdSweep(split: string = 'test.jsonl'): Promise<any[]> {
    const res = await fetch(`${API_BASE}/evaluation/thresholds?split=${split}`);
    if (!res.ok) throw new Error('Failed to fetch threshold sweep');
    return res.json();
  },

  async getEvaluationTransactions(split: string = 'test.jsonl', limit: number = 50): Promise<any> {
    const res = await fetch(`${API_BASE}/evaluation/transactions?split=${split}&limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch evaluation transactions');
    return res.json();
  },

  async getErrorAnalysis(split: string = 'test.jsonl', threshold: number = 75.0): Promise<any> {
    const res = await fetch(`${API_BASE}/evaluation/errors?split=${split}&threshold=${threshold}`);
    if (!res.ok) throw new Error('Failed to fetch error analysis');
    return res.json();
  },

  async getPolicyTiers(split: string = 'validation.jsonl'): Promise<any> {
    const res = await fetch(`${API_BASE}/evaluation/tiers?split=${split}`);
    if (!res.ok) throw new Error('Failed to fetch policy tiers');
    return res.json();
  },

  async requestStepUp(transactionId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/step-up/request?transaction_id=${transactionId}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to initiate step-up challenge');
    return res.json();
  },

  async verifyStepUp(challengeId: string, transactionId: string, success: boolean = true): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/step-up/verify?challenge_id=${challengeId}&transaction_id=${transactionId}&success=${success}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to verify step-up challenge');
    return res.json();
  },

  async getSecurityEvents(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/security/cloudflare/events`);
    if (!res.ok) throw new Error('Failed to fetch security events');
    return res.json();
  },

  async getDataProtectionStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/security/data-protection`);
    if (!res.ok) throw new Error('Failed to fetch data protection status');
    return res.json();
  },

  async testDLP(inputText: string): Promise<any> {
    const res = await fetch(`${API_BASE}/security/dlp/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_text: inputText }),
    });
    if (!res.ok) throw new Error('DLP test request failed');
    return res.json();
  },

  async getExposureEvents(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/exposure/events`);
    if (!res.ok) throw new Error('Failed to fetch exposure events');
    return res.json();
  },

  async getExposureStatistics(): Promise<any> {
    const res = await fetch(`${API_BASE}/exposure/statistics`);
    if (!res.ok) throw new Error('Failed to fetch exposure statistics');
    return res.json();
  },

  async getZombieCards(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/zombie-cards`);
    if (!res.ok) throw new Error('Failed to fetch zombie cards');
    return res.json();
  },

  async getZombieStatistics(): Promise<any> {
    const res = await fetch(`${API_BASE}/zombie-cards/statistics`);
    if (!res.ok) throw new Error('Failed to fetch zombie statistics');
    return res.json();
  },

  async getZombieCardAnalysis(cardId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/zombie-cards/${cardId}/analysis`);
    if (!res.ok) throw new Error(`Failed to fetch analysis for card ${cardId}`);
    return res.json();
  },

  async revokeZombieToken(tokenId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/zombie-cards/tokens/${tokenId}/revoke`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to revoke zombie token ${tokenId}`);
    return res.json();
  },
};
