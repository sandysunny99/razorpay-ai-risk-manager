import { useEffect, useState } from 'react';
import { getComponents } from '../services/api';
import { ComponentsStatus } from '../types/api';
import { getSafeApiError } from '../utils/errors';
import { Notice, Panel, PanelHeader, Tag } from './ui';

function Metric({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div>
      <dt className="text-xs text-ink-subtle">{label}</dt>
      <dd className="font-mono text-base text-ink">{value !== undefined ? value.toFixed(2) : '–'}</dd>
    </div>
  );
}

/** PII engine and ML model card, as reported by GET /health/components. */
export default function ComponentsPanel() {
  const [data, setData] = useState<ComponentsStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getComponents().then(setData).catch((e) => setError(getSafeApiError(e)));
  }, []);

  if (error) return <Notice tone="error" title="Could not load component status">{error}</Notice>;
  if (!data) return null;
  const { pii, ml } = data;

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <Panel>
        <PanelHeader
          title="PII masking"
          subtitle="Customer free text is masked before evidence, the audit trail, the live stream or any LLM"
          action={<Tag tone={pii.engine === 'presidio' ? 'allow' : 'review'}>{pii.engine === 'presidio' ? 'Presidio' : 'Regex fallback'}</Tag>}
        />
        <div className="space-y-2 p-4 text-sm">
          <p className="text-ink-muted">
            {pii.engine === 'presidio'
              ? 'Presidio (MIT) with custom UPI ID and Indian mobile recognizers, plus Aadhaar and PAN. A regex pass runs after it as a safety net.'
              : 'Presidio is not installed, so built-in patterns cover the same entity types (no person-name detection). Install backend/requirements-privacy.txt to enable it.'}
          </p>
          <p className="font-mono text-xs text-ink-subtle">{pii.entities.join('  ')}</p>
        </div>
      </Panel>

      <Panel>
        <PanelHeader
          title="ML second opinion"
          subtitle={`LightGBM ${ml.lightgbm_version ?? ''}, reasons from built-in TreeSHAP`}
          action={
            <Tag tone={!ml.available ? 'block' : ml.escalation_enabled ? 'allow' : 'neutral'}>
              {!ml.available ? 'Unavailable' : ml.escalation_enabled ? `Escalates at ${ml.escalation_threshold}` : 'Advisory only'}
            </Tag>
          }
        />
        <div className="space-y-4 p-4 text-sm">
          <p className="text-ink-muted">
            The model can only send an otherwise allowed payment to human review. It never blocks and never relaxes a rule-based outcome.
          </p>
          {ml.holdout_metrics && (
            <div>
              <p className="text-xs text-ink-subtle">Simulator holdout ({ml.holdout_metrics.n} rows, {Math.round(ml.holdout_metrics.fraud_rate * 100)}% fraud, 2% label noise)</p>
              <dl className="mt-1 grid grid-cols-3 gap-3">
                <Metric label="PR-AUC" value={ml.holdout_metrics.pr_auc} />
                <Metric label="Recall at 1% FPR" value={ml.holdout_metrics.recall_at_1pct_fpr} />
                <Metric label="Recall at 5% FPR" value={ml.holdout_metrics.recall_at_5pct_fpr} />
              </dl>
            </div>
          )}
          {ml.why_not_evaluation_set && (
            <p className="text-xs text-ink-subtle">
              Not trained on the bundled evaluation set: its labels follow one rule exactly ({ml.why_not_evaluation_set.label_rule}) and velocity alone
              separates them, which taught an earlier model to ignore zombie tokens.
            </p>
          )}
          {ml.caveat && <Notice tone="warn">{ml.caveat}</Notice>}
        </div>
      </Panel>
    </div>
  );
}
