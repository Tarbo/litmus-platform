'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { ExecutiveSummary } from '@/types';

const initial: ExecutiveSummary = {
  passed: 0,
  failed: 0,
  running: 0,
  inconclusive: 0,
  terminated_without_cause: 0,
};

export default function HomePage() {
  const [summary, setSummary] = useState<ExecutiveSummary>(initial);

  useEffect(() => {
    apiGet<ExecutiveSummary>('/experiments/executive-summary').then(setSummary).catch(() => setSummary(initial));
  }, []);

  return (
    <section>
      <h1>Litmus Executive Summary</h1>
      <p className="muted">Production experiments at a glance.</p>
      <div className="grid cols-5">
        <SummaryCard title="Passed" value={summary.passed} />
        <SummaryCard title="Failed" value={summary.failed} />
        <SummaryCard title="Running" value={summary.running} />
        <SummaryCard title="Inconclusive" value={summary.inconclusive} />
        <SummaryCard title="Terminated" value={summary.terminated_without_cause} />
      </div>
    </section>
  );
}

function SummaryCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="card">
      <h4>{title}</h4>
      <div style={{ fontSize: '2rem', fontWeight: 700 }}>{value}</div>
    </div>
  );
}
