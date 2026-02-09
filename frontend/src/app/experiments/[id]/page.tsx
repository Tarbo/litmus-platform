'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiGet, apiPost, wsExperimentUrl } from '@/lib/api';
import type { Experiment, ExperimentReport } from '@/types';

export default function ExperimentDetailPage({ params }: { params: { id: string } }) {
  const experimentId = params.id;
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [reason, setReason] = useState('');
  const wsUrl = useMemo(() => wsExperimentUrl(experimentId), [experimentId]);

  useEffect(() => {
    apiGet<Experiment>(`/experiments/${experimentId}`).then(setExperiment).catch(() => setExperiment(null));
    apiGet<ExperimentReport>(`/experiments/${experimentId}/report`).then(setReport).catch(() => setReport(null));
  }, [experimentId]);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ExperimentReport;
        setReport(data);
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
          <p>Confidence: {(report.confidence * 100).toFixed(1)}%</p>
          <p>Sample Progress: {(report.sample_progress * 100).toFixed(1)}%</p>
          <p>Diff-in-Diff Delta: {report.diff_in_diff_delta === null ? 'N/A (advanced mode)' : report.diff_in_diff_delta}</p>
          <p className="muted">Last Updated: {new Date(report.last_updated_at).toLocaleString()}</p>
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
    </section>
  );
}
