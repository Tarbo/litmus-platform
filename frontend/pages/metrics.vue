<template>
  <section class="page">
    <h2 class="page-title">Metrics</h2>
    <article class="card" v-if="pending">
      <p>Loading guardrails...</p>
    </article>
    <article class="card" v-else-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>
    <article class="card" v-else>
      <h3 class="section-title">Guardrail Metrics</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Experiment</th>
            <th>Metric</th>
            <th>Value</th>
            <th>Threshold</th>
            <th>Direction</th>
            <th>Status</th>
            <th>Observed At</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in rows" :key="item.id">
            <td>
              <NuxtLink :to="`/experiments/${item.experimentId}`">{{ item.experimentName }}</NuxtLink>
            </td>
            <td>{{ item.name }}</td>
            <td>{{ item.value }}</td>
            <td>{{ item.thresholdValue }}</td>
            <td>{{ item.direction }}</td>
            <td>{{ item.status }}</td>
            <td>{{ formatDate(item.observedAt) }}</td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="7">No guardrail metrics found yet.</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { Experiment, GuardrailMetric } from '~/types'

interface GuardrailRow {
  id: string
  experimentId: string
  experimentName: string
  name: string
  value: number
  thresholdValue: number
  direction: string
  status: string
  observedAt: string
}

const { listExperiments, listGuardrails } = useApi()

const rows = ref<GuardrailRow[]>([])
const pending = ref(true)
const errorMessage = ref('')

const formatDate = (value: string) => new Date(value).toLocaleString()

const load = async () => {
  pending.value = true
  errorMessage.value = ''
  try {
    const experiments = await listExperiments()
    const guardrailsByExperiment = await Promise.all(
      experiments.map(async (experiment: Experiment) => {
        const metrics = await listGuardrails(experiment.id)
        return {
          experiment,
          metrics,
        }
      })
    )
    rows.value = guardrailsByExperiment
      .flatMap(({ experiment, metrics }: { experiment: Experiment; metrics: GuardrailMetric[] }) =>
        metrics.map((metric) => ({
          id: metric.id,
          experimentId: experiment.id,
          experimentName: experiment.name,
          name: metric.name,
          value: metric.value,
          thresholdValue: metric.threshold_value,
          direction: String(metric.direction).toUpperCase(),
          status: String(metric.status).toUpperCase(),
          observedAt: metric.observed_at,
        }))
      )
      .sort((a, b) => new Date(b.observedAt).getTime() - new Date(a.observedAt).getTime())
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    pending.value = false
  }
}

onMounted(load)
</script>
