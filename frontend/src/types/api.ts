export type ProviderStatus =
  | 'HEALTHY'
  | 'DEGRADED'
  | 'UNAVAILABLE'
  | 'MISCONFIGURED'
  | 'NOT VERIFIED / CONTRACT TESTED';

export type Decision = 'ALLOW' | 'REVIEW' | 'BLOCK' | 'QUARANTINE' | 'UNAVAILABLE';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface SystemHealth {
  status: string;
  service: string;
}

export interface ProviderChainRow {
  name: string;
  configured: boolean;
  model: string | null;
  status: string;
  latency_ms: number | null;
  detail: string | null;
  checked_at: number | null;
}

export interface ProviderHealth {
  primary: ProviderStatus;
  secondary: ProviderStatus;
  fallback: ProviderStatus;
  chain?: ProviderChainRow[];
  scope?: 'flagged' | 'all';
  budget?: { used_last_minute: number; limit_per_minute: number };
}

/** Mirrors backend/risk/models.py::RiskFactor */
export interface RiskFactor {
  name: string;
  description: string;
  score_impact: number;
}

/** Mirrors backend/risk/models.py::RiskAssessment */
export interface RiskAssessment {
  risk_score: number;
  risk_level: RiskLevel | string;
  confidence?: number;
  risk_factors: RiskFactor[];
  evidence_ids: string[];
  correlation_id?: string;
  timestamp?: number;
}

export interface ZombieSignal {
  impact: string;
  severity: RiskLevel | string;
  recommendation: string;
}

export interface AiAdvisory {
  provider: string;
  recommended_action: string;
  evidence_ids?: string[];
}

/** Response of POST /webhooks/payment */
export interface TransactionResponse {
  correlation_id: string;
  event_id: string;
  decision: Decision | string;
  risk_assessment: RiskAssessment;
  evidence_ids?: string[];
  audit_id: string;
  audit_hash?: string;
  zombie_signal?: ZombieSignal | null;
  ai_advisory?: AiAdvisory;
}

/** Metadata-only audit projection from GET /audit and GET /audit/{id} */
export interface AuditSummaryItem {
  audit_id: string;
  event_id: string;
  merchant_id: string;
  correlation_id: string;
  timestamp: number;
  decision: Decision | string | null;
  risk_score?: number | null;
  risk_level?: string | null;
  zombie_detected?: boolean;
  reason_codes?: string[];
  record_hash?: string;
  resolution?: { action: 'APPROVE' | 'DECLINE'; timestamp: number } | null;
}

export interface AuditRecord extends AuditSummaryItem {
  chain_verified?: boolean;
}

/** Kept for backwards compatibility with earlier imports. */
export type AuditRecordResponse = AuditRecord;

export interface AuditList {
  items: AuditSummaryItem[];
}

export interface AuditStats {
  total: number;
  decisions: Record<'ALLOW' | 'REVIEW' | 'BLOCK' | 'QUARANTINE', number>;
  zombie_detected: number;
  average_risk_score: number | null;
  chain_verified: boolean;
}

/** One pipeline outcome pushed over the /live/events SSE stream (metadata only). */
export interface LiveEvent {
  seq: number;
  ts: number; // epoch ms
  tenant_id: string;
  source: 'generator' | 'api' | 'razorpay' | string;
  scenario?: string;
  outcome: 'DECIDED' | 'REJECTED' | 'RESOLVED' | 'EXPOSURE';
  event_id?: string | null;
  correlation_id?: string;
  amount?: number | null;
  currency?: string | null;
  event_type?: string | null;
  latency_ms?: number;
  // DECIDED
  decision?: Decision | string;
  risk_score?: number;
  risk_level?: string;
  risk_factors?: string[];
  zombie?: ZombieSignal | null;
  ai_provider?: string;
  audit_id?: string;
  threat?: ThreatMatch[];
  ml?: MlAssessment | null;
  ai?: { status: string | null; reason: string | null; recommended_action: string | null; explanation: string | null } | null;
  pii_masked?: string[];
  // RESOLVED (analyst outcome for a REVIEW decision)
  resolves?: string;
  resolution?: 'APPROVE' | 'DECLINE';
  // EXPOSURE (card exposure report revoked linked tokens)
  tokens_revoked?: number;
  findings?: number;
  // REJECTED
  http_status?: number;
  rejected_stage?: string;
  reason?: string;
}

export interface GeneratorStatus {
  running: boolean;
  tenant_id: string;
  rate_per_sec: number;
  attack_ratio: number;
  risky_ratio: number;
  emitted: number;
  started_at: number | null;
  by_scenario: Record<string, number>;
}

export interface LiveSnapshot {
  events: LiveEvent[];
  subscribers: number;
  generator: GeneratorStatus | null;
}

export interface RazorpayStatus {
  configured: boolean;
  tenant_id: string;
  webhook_path: string;
  supported_events: string[];
  received: number;
  verified: number;
  rejected_signature: number;
  ignored: number;
  last_event_at: number | null;
}

export interface ThreatMatch {
  indicator_type: 'ip' | 'token' | string;
  indicator: string;
  source: string;
  category: string;
  confidence: number;
}

export interface ThreatSource {
  name: string;
  category: string;
  confidence: number;
  url: string | null;
  license: string;
  enabled: boolean;
  indicators: number;
  last_refresh: number | null;
  last_error: string | null;
}

export interface IntelStatus {
  live_feeds_enabled: boolean;
  sources: ThreatSource[];
  lookups: number;
  hits: number;
  learned: { revoked_tokens: number; watched_ips: number };
}

export interface IntelMatchLog {
  event_id: string;
  ts: number;
  matches: ThreatMatch[];
}

export interface ExposureSummary {
  configured: boolean;
  exposed_fingerprints: number;
  tokens_revoked_via_exposure: number;
  reports: { source: string; reported_at: number; findings: number; new: number; tokens_revoked: number }[];
  recent: { fingerprint: string; source: string; reference: string; observed_at: number; confidence: number }[];
}

export interface GatewayStatus {
  configured: boolean;
  tenant_id: string;
  webhook_path: string;
  supported_events: string[];
  received: number;
  verified: number;
  rejected_signature: number;
  ignored: number;
  duplicates?: number;
  last_event_at: number | null;
  experimental?: boolean;
  require_v2?: boolean;
}

export interface MlReason {
  feature: string;
  direction: 'raises' | 'lowers';
  contribution: number;
  value: number | null;
}

export interface MlAssessment {
  model: string;
  probability: number;
  reasons: MlReason[];
  escalated?: boolean;
  escalation_threshold?: number;
}

interface Metrics {
  pr_auc: number;
  roc_auc: number;
  recall_at_1pct_fpr: number;
  recall_at_5pct_fpr: number;
  fraud_rate: number;
  n: number;
}

export interface ComponentsStatus {
  pii: { engine: 'presidio' | 'regex'; error: string | null; entities: string[] };
  ml: {
    available: boolean;
    error: string | null;
    escalation_enabled: boolean;
    escalation_threshold: number;
    lightgbm_version?: string;
    training_data?: string;
    holdout_metrics?: Metrics;
    holdout_metrics_live_fields_missing?: Metrics;
    cross_dataset_metrics_evaluation_test?: Metrics;
    probes?: Record<string, number>;
    why_not_evaluation_set?: { label_rule: string; label_rule_agreement: number; velocity_shortcut: Record<string, number> };
    caveat?: string;
  };
}
