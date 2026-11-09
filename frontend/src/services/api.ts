import axios from 'axios';
import {
  AuditList,
  AuditRecord,
  AuditRecordResponse,
  AuditStats,
  GeneratorStatus,
  LiveSnapshot,
  ProviderHealth,
  RazorpayStatus,
  SystemHealth,
  TransactionResponse,
} from '../types/api';

// Dev server talks to the local API; a production build is served by the API itself (same origin).
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '');

/** DEMO TENANT CONTEXT — production authentication is not connected in this prototype. */
export const DEMO_TENANT = 'tenant_123';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'x-tenant-id': DEMO_TENANT },
});

export interface WebhookDemoData {
  amount: number;
  currency: string;
  ip_address?: string;
  user_input?: string;
  note?: string;
  card_lifecycle?: 'ACTIVE' | 'EXPIRED' | 'REPLACED';
  recent_reuse_count?: number;
  trusted_compromise_assertion?: boolean;
  velocity_1h?: number;
}

export interface WebhookDemoPayload {
  event_id: string;
  merchant_id: string;
  timestamp: number;
  event_type: string;
  data: WebhookDemoData;
  token?: string;
}

export interface DemoRunOptions {
  /** Replace the server signature with a forged one. */
  badHmac?: boolean;
  /** Send the request under a different tenant header than the signed merchant_id. */
  badTenant?: boolean;
  /** Deliver the identical signed request twice (webhook retry / replay). Returns the 2nd result. */
  deliverTwice?: boolean;
}

interface DemoSignResponse {
  signature: string;
  payload: unknown;
  signed_body?: string;
}

/**
 * Signs a payload with the backend demo signer, then posts it to the protected webhook.
 * The exact signed bytes are sent verbatim — re-serializing in JS would alter floats and break HMAC.
 */
export const processWebhookDemo = async (
  payload: WebhookDemoPayload,
  options: DemoRunOptions = {},
): Promise<TransactionResponse> => {
  const signRes = await api.post<DemoSignResponse>('/webhooks/demo/sign', payload);
  const body = signRes.data.signed_body ?? JSON.stringify(signRes.data.payload);
  const signature = options.badHmac ? 'forged_signature_0000' : signRes.data.signature;

  const send = () =>
    api.post<TransactionResponse>('/webhooks/payment', body, {
      headers: {
        'content-type': 'application/json',
        'x-signature': signature,
        'x-tenant-id': options.badTenant ? 'tenant_attacker_999' : DEMO_TENANT,
      },
      transformRequest: [(data) => data],
    });

  if (options.deliverTwice) {
    await send();
  }
  const res = await send();
  return res.data;
};

export const getHealth = async (): Promise<SystemHealth> => (await api.get('/health')).data;

export const getProviderHealth = async (): Promise<ProviderHealth> => (await api.get('/health/providers')).data;

export const getAudit = async (auditId: string): Promise<AuditRecord> =>
  (await api.get(`/audit/${encodeURIComponent(auditId)}`)).data;

export const getAuditRecord = async (auditId: string): Promise<AuditRecordResponse> => getAudit(auditId);

export const listAuditRecords = async (limit = 25): Promise<AuditList> =>
  (await api.get('/audit', { params: { limit } })).data;

export const getAuditStats = async (): Promise<AuditStats> => (await api.get('/audit/summary')).data;

// ── Real-time ────────────────────────────────────────────────────────────────────────────

/** EventSource cannot send headers, so the demo tenant travels as a query parameter. */
export const liveStreamUrl = (tenant = DEMO_TENANT): string =>
  `${API_BASE_URL}/live/events?tenant=${encodeURIComponent(tenant)}`;

export const getLiveSnapshot = async (limit = 300): Promise<LiveSnapshot> =>
  (await api.get('/live/snapshot', { params: { limit } })).data;

export interface GeneratorUpdate {
  running?: boolean;
  rate_per_sec?: number;
  attack_ratio?: number;
  risky_ratio?: number;
}

export const updateGenerator = async (update: GeneratorUpdate): Promise<GeneratorStatus> =>
  (await api.post('/live/generator', update)).data;

export const getRazorpayStatus = async (): Promise<RazorpayStatus> =>
  (await api.get('/integrations/razorpay/status')).data;
