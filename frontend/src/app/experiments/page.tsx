'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { CondensedPerformance } from '@/types';

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<CondensedPerformance[]>([]);

  useEffect(() => {
    apiGet<CondensedPerformance[]>('/experiments/running').then(setExperiments).catch(() => setExperiments([]));
  }, []);

  return (
    <section>
      <h1>Running Experiments</h1>
      <p className="muted">Condensed performance beside each active experiment.</p>
      <div className="grid cols-2">
        {experiments.map((exp) => (
          <article key={exp.experiment_id} className="card">
            <h3>{exp.name}</h3>
            <p className="badge">{exp.status}</p>
            <p className="muted">Exposures: {exp.exposures} | Conversions: {exp.conversions}</p>
            <p>Conversion Rate: {(exp.conversion_rate * 100).toFixed(2)}%</p>
            <p>Uplift vs Control: {(exp.uplift_vs_control * 100).toFixed(2)}%</p>
            <p>Confidence: {(exp.confidence * 100).toFixed(1)}%</p>
            <p>Sample Progress: {(exp.sample_progress * 100).toFixed(1)}%</p>
            <div className="actions">
              <Link className="link" href={`/experiments/${exp.experiment_id}`}>
                View Full Report
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
