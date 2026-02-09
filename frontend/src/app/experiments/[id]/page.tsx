'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiGet, apiPost, wsExperimentUrl } from '@/lib/api';
import type { Experiment, ExperimentReport, GuardrailMetric, ReportSnapshot } from '@/types';

export default function ExperimentDetailPage({ params }: { params: { id: string } }) {
  const experimentId = params.id;
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [snapshots, setSnapshots] = useState<ReportSnapshot[]>([]);
  const [guardrails, setGuardrails] = useState<GuardrailMetric[]>([]);
  const [reason, setReason] = useState('');
  const [guardrailName, setGuardrailName] = useState('p95_latency_ms');
  const [guardrailValue, setGuardrailValue] = useState(0);
  const [guardrailThreshold, setGuardrailThreshold] = useState(350);
  const [guardrailDirection, setGuardrailDirection] = useState<'max' | 'min'>('max');
  const wsUrl = useMemo(() => wsExperimentUrl(experimentId), [experimentId]);

  useEffect(() => {
    apiGet<Experiment>(`/experiments/${experimentId}`).then(setExperiment).catch(() => setExperiment(null));
    apiGet<ExperimentReport>(`/experiments/${experimentId}/report`).then(setReport).catch(() => setReport(null));
    apiGet<ReportSnapshot[]>(`/experiments/${experimentId}/snapshots`).then(setSnapshots).catch(() => setSnapshots([]));
    apiGet<GuardrailMetric[]>(`/metrics/guardrails/${experimentId}`).then(setGuardrails).catch(() => setGuardrails([]));
  }, [experimentId]);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ExperimentReport;
        setReport(data);
        apiGet<ReportSnapshot[]>(`/experiments/${experimentId}/snapshots`).then(setSnapshots).catch(() => setSnapshots([]));
      } catch {
        // Ignore malformed messages.
      }
    };
    return () => ws.close();
  }, [wsUrl]);

  async function terminate() {
    await apiPost<Experiment>(`/experiments/${experimentId}/terminate`, { reason: reason || null });
    const updated = await apiGet<Experiment>(`/experiments/${experimentId}`);
    setExperiment(updated);
  }

  async function submitGuardrailMetric() {
    const created = await apiPost<GuardrailMetric>('/metrics/guardrails', {
      experiment_id: experimentId,
      name: guardrailName,
      value: guardrailValue,
      threshold_value: guardrailThreshold,
      direction: guardrailDirection,
    });
    setGuardrails((prev) => [created, ...prev]);
    const updatedReport = await apiGet<ExperimentReport>(`/experiments/${experimentId}/report`);
    setReport(updatedReport);
    const refreshedSnapshots = await apiGet<ReportSnapshot[]>(`/experiments/${experimentId}/snapshots`);
    setSnapshots(refreshedSnapshots);
  }

  if (!experiment) {
    return <p>Loading experiment...</p>;
  }

  return (
    <section className="grid" style={{ gap: '1rem' }}>
      <div className="card">
        <h1>{experiment.name}</h1>
        <p className="muted">{experiment.hypothesis}</p>
        <p>
          Status: <span className="badge">{experiment.status}</span>
        </p>
        <p>MDE: {(experiment.mde * 100).toFixed(2)}%</p>
        <p>Sample Size Needed: {experiment.sample_size_required}</p>
      </div>

      {report && (
        <div className="card">
          <h3>Full Progress Report (Realtime)</h3>
          <p>Exposures: {report.exposures}</p>
          <p>Conversions: {report.conversions}</p>
          <p>Control CR: {(report.control_conversion_rate * 100).toFixed(2)}%</p>
          <p>Treatment CR: {(report.treatment_conversion_rate * 100).toFixed(2)}%</p>
          <p>Uplift: {(report.uplift_vs_control * 100).toFixed(2)}%</p>
          <p>
            Uplift 95% CI: {(report.uplift_ci_lower * 100).toFixed(2)}% to {(report.uplift_ci_upper * 100).toFixed(2)}%
          </p>
          <p>p-value: {report.p_value.toFixed(4)}</p>
          <p>Confidence: {(report.confidence * 100).toFixed(1)}%</p>
          <p>Recommendation: <span className="badge">{report.recommendation}</span></p>
          <p>Guardrails Breached: {report.guardrails_breached}</p>
          <p>Sample Progress: {(report.sample_progress * 100).toFixed(1)}%</p>
          <p>Diff-in-Diff Delta: {report.diff_in_diff_delta === null ? 'N/A (advanced mode)' : report.diff_in_diff_delta}</p>
          <p className="muted">Last Updated: {new Date(report.last_updated_at).toLocaleString()}</p>
        </div>
      )}

      {report && (
        <div className="card">
          <h3>Guardrail Status</h3>
          {report.guardrails.length === 0 && <p className="muted">No guardrail observations yet.</p>}
          {report.guardrails.map((guardrail) => (
            <p key={guardrail.name}>
              {guardrail.name}: {guardrail.value} ({guardrail.direction} {guardrail.threshold_value}){' '}
              <span className="badge">{guardrail.status}</span>
            </p>
          ))}
        </div>
      )}

      <div className="card">
        <h3>Log Guardrail Metric</h3>
        <label htmlFor="guardrail-name">Metric Name</label>
        <input id="guardrail-name" value={guardrailName} onChange={(e) => setGuardrailName(e.target.value)} />
        <label htmlFor="guardrail-value">Observed Value</label>
        <input
          id="guardrail-value"
          type="number"
          value={guardrailValue}
          onChange={(e) => setGuardrailValue(Number(e.target.value))}
        />
        <label htmlFor="guardrail-threshold">Threshold Value</label>
        <input
          id="guardrail-threshold"
          type="number"
          value={guardrailThreshold}
          onChange={(e) => setGuardrailThreshold(Number(e.target.value))}
        />
        <label htmlFor="guardrail-direction">Direction</label>
        <select
          id="guardrail-direction"
          value={guardrailDirection}
          onChange={(e) => setGuardrailDirection(e.target.value as 'max' | 'min')}
        >
          <option value="max">max (value should stay under threshold)</option>
          <option value="min">min (value should stay above threshold)</option>
        </select>
        <div style={{ marginTop: '0.7rem' }}>
          <button className="primary" onClick={submitGuardrailMetric}>
            Add Guardrail Observation
          </button>
        </div>
      </div>

      {report && (
        <div className="card">
          <h3>Variant Performance (Pre/Post)</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Variant</th>
                  <th style={{ textAlign: 'left' }}>Post Exposures</th>
                  <th style={{ textAlign: 'left' }}>Post CR</th>
                  <th style={{ textAlign: 'left' }}>Pre Exposures</th>
                  <th style={{ textAlign: 'left' }}>Pre CR</th>
                </tr>
              </thead>
              <tbody>
                {report.variant_performance.map((variant) => (
                  <tr key={variant.variant_id}>
                    <td>{variant.variant_name}</td>
                    <td>{variant.post_exposures}</td>
                    <td>{(variant.post_conversion_rate * 100).toFixed(2)}%</td>
                    <td>{variant.pre_exposures}</td>
                    <td>{(variant.pre_conversion_rate * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {experiment.status === 'running' && (
        <div className="card">
          <h3>Terminate Experiment</h3>
          <p className="muted">This will stop the experiment and release active cohort assignments.</p>
          <label htmlFor="reason">Reason (optional)</label>
          <textarea id="reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3} />
          <div style={{ marginTop: '0.7rem' }}>
            <button className="danger" onClick={terminate}>
              Terminate and Release Cohort
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h3>Report Snapshots</h3>
        {snapshots.length === 0 && <p className="muted">No snapshots captured yet.</p>}
        {snapshots.slice(0, 10).map((snapshot) => (
          <p key={snapshot.id}>
            {new Date(snapshot.created_at).toLocaleString()} | recommendation: {snapshot.snapshot.recommendation} |
            confidence: {(snapshot.snapshot.confidence * 100).toFixed(1)}%
          </p>
        ))}
      </div>
    </section>
  );
}
