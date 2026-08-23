export interface FactorItem {
  name: string;
  weight: number;
  score: number;
  contribution: number;
  reason: string;
}

export interface InvestigationStep {
  timestamp: string;
  stage: string;
  description: string;
  tool_used?: string;
  status: 'SUCCESS' | 'WARNING' | 'FAILED' | 'INFO';
  data?: Record<string, any>;
}

export interface ToolAuditItem {
  tool: string;
  selected: boolean;
  reason: string;
}

export interface InvestigationResponse {
  investigation_id: string;
  initial_risk: number;
  final_risk: number;
  initial_severity: string;
  final_severity: string;
  risk_level: string;
  detection_status: string;
  response_tier: string;
  policy_decision: string;
  recommended_action: string;
  investigation_level: number;
  action_taken: string;
  policy_status: string;
  verification_status: string;
  case_id?: string;
  timeline: InvestigationStep[];
  agent_reasoning: string;
  explainable_factors: FactorItem[];
  tools_requested?: string[];
  tools_executed?: string[];
  tools_skipped?: string[];
  tool_audit?: ToolAuditItem[];
}

export interface PolicyTierDistribution {
  split: string;
  total_records: number;
  tier_counts: {
    LOW: number;
    MONITOR: number;
    STEP_UP: number;
    REVIEW: number;
    AUTO_REMEDIATE: number;
  };
  action_counts: Record<string, number>;
}

export interface CardItem {
  card_id: string;
  customer_id: string;
  masked_pan: string;
  bin: string;
  cardholder_name: string;
  expiry_month: number;
  expiry_year: number;
  is_expired: boolean;
  status: string;
  failed_attempts: number;
  previous_fraud_count: number;
  active_token_count: number;
  exposure_count: number;
  current_risk_score: number;
}

export interface TokenItem {
  token_id: string;
  card_id: string;
  customer_id: string;
  merchant_id: string;
  status: string;
  token_age_days: number;
  usage_count: number;
  last_used_at: string;
  is_zombie: boolean;
  zombie_reason?: string;
}

export interface ZombieTokenAlert {
  token_id: string;
  card_id: string;
  masked_pan: string;
  card_status: string;
  is_card_expired: boolean;
  token_status: string;
  last_used: string;
  risk_level: string;
  reason: string;
}

export interface SecurityCase {
  case_id: string;
  severity: string;
  card_id: string;
  token_id?: string;
  customer_id: string;
  merchant_id: string;
  risk_score: number;
  reason: string;
  status: string;
  assigned_to: string;
  actions_taken: string[];
  timeline: Record<string, any>[];
  created_at: string;
}

export interface AuditEvent {
  event_id: string;
  actor: string;
  agent_decision: string;
  risk_score: number;
  policy_evaluated: string;
  tool_used?: string;
  action_requested?: string;
  action_executed?: string;
  verification_result?: string;
  details: Record<string, any>;
  created_at: string;
}

export interface OverviewMetrics {
  cards_monitored: number;
  tokens_monitored: number;
  active_zombie_tokens: number;
  high_risk_cards: number;
  critical_incidents: number;
  exposure_events_count: number;
  open_cases_count: number;
  system_status: string;
  dry_run_mode: boolean;
}

export interface ScenarioItem {
  id: string;
  name: string;
  description: string;
  txn_id?: string;
  card_masked?: string;
  expected_initial_risk?: number | string;
  expected_final_risk?: number | string;
}

export interface EvaluationMetrics {
  threshold: number;
  total_samples: number;
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  specificity: number;
  fpr: number;
  fnr: number;
  fp_cost_unit: number;
  fn_cost_unit: number;
  expected_cost: number;
}

export interface AblationItem {
  model_name: string;
  precision: number;
  recall: number;
  f1: number;
  fpr: number;
  fnr: number;
  expected_cost: number;
}

export interface ThresholdSweepItem {
  threshold: number;
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
  expected_cost: number;
}

export interface EvaluationTransactionItem {
  transaction_id: string;
  merchant_id: string;
  customer_id: string;
  card_masked: string;
  amount: number;
  currency: string;
  country: string;
  customer_country: string;
  velocity_10m: number;
  card_exposed: boolean;
  exposure_confidence: number;
  exposure_source: string;
  token_active: boolean;
  is_zombie_token: boolean;
  calculated_risk_score: number;
  severity: string;
  recommended_action: string;
  label: number;
}
