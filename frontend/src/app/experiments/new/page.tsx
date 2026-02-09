'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { apiPost } from '@/lib/api';
import type { Experiment } from '@/types';

export default function NewExperimentPage() {
  const router = useRouter();
  const [name, setName] = useState('Checkout Button Experiment');
  const [hypothesis, setHypothesis] = useState('Green CTA improves conversion relative to blue CTA');
  const [mde, setMde] = useState(0.05);

  async function createExperiment() {
    const payload = {
      name,
      hypothesis,
      mde,
      baseline_rate: 0.1,
      alpha: 0.05,
      power: 0.8,
      variants: [
        { name: 'control', traffic_allocation: 0.5 },
        { name: 'treatment', traffic_allocation: 0.5 },
      ],
    };
    const experiment = await apiPost<Experiment>('/experiments', payload);
    router.push(`/experiments/${experiment.id}`);
  }

  return (
    <section className="card">
      <h1>Create Experiment</h1>
      <label htmlFor="name">Name</label>
      <input id="name" value={name} onChange={(e) => setName(e.target.value)} />
      <label htmlFor="hypothesis">Hypothesis</label>
      <textarea id="hypothesis" value={hypothesis} onChange={(e) => setHypothesis(e.target.value)} rows={3} />
      <label htmlFor="mde">MDE (0-1)</label>
      <input id="mde" type="number" step="0.01" value={mde} onChange={(e) => setMde(Number(e.target.value))} />
      <div style={{ marginTop: '1rem' }}>
        <button className="primary" onClick={createExperiment}>
          Create and Start
        </button>
      </div>
    </section>
  );
}
