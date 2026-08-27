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

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

type ErrorListener = (errorMsg: string) => void;
let errorListener: ErrorListener | null = null;

export const setApiErrorListener = (listener: ErrorListener | null) => {
  errorListener = listener;
};

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      let detail = res.statusText || 'API request failed';
      try {
        const parsed = JSON.parse(errText);
        detail = parsed.detail || parsed.message || detail;
      } catch {
        if (errText) detail = errText;
      }
      const message = `${detail} (${res.status})`;
      if (errorListener) errorListener(message);
      throw new Error(message);
    }
    return res.json();
  } catch (err: any) {
    if (errorListener && !err.message?.includes('(')) {
      errorListener(err.message || 'Network connection failed');
    }
    throw err;
  }
}

export const api = {
  async getOverview(): Promise<OverviewMetrics> {
    return fetchJson<OverviewMetrics>(`${API_BASE}/risk/overview`);
  },

  async triggerInvestigation(txnId?: string): Promise<InvestigationResponse> {
    return fetchJson<InvestigationResponse>(`${API_BASE}/risk/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transaction_id: txnId }),
    });
  },

  async triggerGoldenDemo(): Promise<InvestigationResponse> {
    return fetchJson<InvestigationResponse>(`${API_BASE}/demo/trigger-golden-scenario`, {
      method: 'POST',
    });
  },

  async triggerHighRiskDemo(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/demo/trigger-high-risk-transaction`, {
      method: 'POST',
    });
  },

  async triggerStepUpDemo(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/demo/trigger-step-up-challenge`, {
      method: 'POST',
    });
  },

  async triggerCardExposureDemo(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/demo/trigger-card-exposure`, {
      method: 'POST',
    });
  },

  async triggerPolicyDenialDemo(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/demo/trigger-policy-denial-scenario`, {
      method: 'POST',
    });
  },

  async triggerPromptInjectionDemo(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/demo/trigger-prompt-injection-scenario`, {
      method: 'POST',
    });
  },

  async verifyAuditChain(): Promise<{
    valid: boolean;
    total_events: number;
    status: string;
    tampered_events: any[];
    head_hash?: string;
  }> {
    return fetchJson(`${API_BASE}/audit/verify`);
  },

  async getScenarios(): Promise<ScenarioItem[]> {
    return fetchJson<ScenarioItem[]>(`${API_BASE}/demo/scenarios`);
  },

  async resetData(): Promise<{ status: string; message: string }> {
    return fetchJson<{ status: string; message: string }>(`${API_BASE}/demo/reset-data`, {
      method: 'POST',
    });
  },

  async getCards(): Promise<CardItem[]> {
    return fetchJson<CardItem[]>(`${API_BASE}/cards`);
  },

  async getTokens(): Promise<TokenItem[]> {
    return fetchJson<TokenItem[]>(`${API_BASE}/tokens`);
  },

  async getZombieTokens(): Promise<ZombieTokenAlert[]> {
    return fetchJson<ZombieTokenAlert[]>(`${API_BASE}/tokens/zombies`);
  },

  async revokeToken(tokenId: string): Promise<any> {
    return fetchJson<any>(`${API_BASE}/tokens/${tokenId}/revoke`, {
      method: 'POST',
    });
  },

  async getCases(): Promise<SecurityCase[]> {
    return fetchJson<SecurityCase[]>(`${API_BASE}/cases`);
  },

  async getAuditEvents(limit: number = 50, offset: number = 0): Promise<AuditEvent[]> {
    return fetchJson<AuditEvent[]>(`${API_BASE}/audit/events?limit=${limit}&offset=${offset}`);
  },

  async getEvaluationMetrics(split: string = 'test.jsonl', threshold: number = 75.0): Promise<any> {
    return fetchJson<any>(`${API_BASE}/evaluation/metrics?split=${split}&threshold=${threshold}`);
  },

  async getAblationStudy(split: string = 'test.jsonl'): Promise<any[]> {
    return fetchJson<any[]>(`${API_BASE}/evaluation/ablation?split=${split}`);
  },

  async getThresholdSweep(split: string = 'test.jsonl'): Promise<any[]> {
    return fetchJson<any[]>(`${API_BASE}/evaluation/thresholds?split=${split}`);
  },

  async getEvaluationTransactions(split: string = 'test.jsonl', limit: number = 50): Promise<any> {
    return fetchJson<any>(`${API_BASE}/evaluation/transactions?split=${split}&limit=${limit}`);
  },

  async getErrorAnalysis(split: string = 'test.jsonl', threshold: number = 75.0): Promise<any> {
    return fetchJson<any>(`${API_BASE}/evaluation/errors?split=${split}&threshold=${threshold}`);
  },

  async getPolicyTiers(split: string = 'validation.jsonl'): Promise<any> {
    return fetchJson<any>(`${API_BASE}/evaluation/tiers?split=${split}`);
  },

  async requestStepUp(transactionId: string): Promise<any> {
    return fetchJson<any>(`${API_BASE}/risk/step-up/request?transaction_id=${transactionId}`, {
      method: 'POST',
    });
  },

  async verifyStepUp(challengeId: string, transactionId: string, success: boolean = true): Promise<any> {
    return fetchJson<any>(
      `${API_BASE}/risk/step-up/verify?challenge_id=${challengeId}&transaction_id=${transactionId}&success=${success}`,
      { method: 'POST' }
    );
  },

  async getSecurityEvents(): Promise<any[]> {
    return fetchJson<any[]>(`${API_BASE}/security/cloudflare/events`);
  },

  async getDataProtectionStatus(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/security/data-protection`);
  },

  async testDLP(inputText: string): Promise<any> {
    return fetchJson<any>(`${API_BASE}/security/dlp/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_text: inputText }),
    });
  },

  async getExposureEvents(): Promise<any[]> {
    return fetchJson<any[]>(`${API_BASE}/exposure/events`);
  },

  async getExposureStatistics(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/exposure/statistics`);
  },

  async getZombieCards(): Promise<any[]> {
    return fetchJson<any[]>(`${API_BASE}/zombie-cards`);
  },

  async getZombieStatistics(): Promise<any> {
    return fetchJson<any>(`${API_BASE}/zombie-cards/statistics`);
  },

  async getZombieCardAnalysis(cardId: string): Promise<any> {
    return fetchJson<any>(`${API_BASE}/zombie-cards/${cardId}/analysis`);
  },

  async revokeZombieToken(tokenId: string): Promise<any> {
    return fetchJson<any>(`${API_BASE}/zombie-cards/tokens/${tokenId}/revoke`, {
      method: 'POST',
    });
  },
};
