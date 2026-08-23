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
};
