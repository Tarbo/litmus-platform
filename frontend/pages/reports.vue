<template>
  <section class="page">
    <h2 class="page-title">Reports</h2>
    <article class="card" v-if="pending">
      <p>Loading reports...</p>
    </article>
    <article class="card" v-else-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>
    <template v-else>
      <article class="card">
        <h3 class="section-title">Running Experiments</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Experiment</th>
              <th>Status</th>
              <th>Exposures</th>
              <th>Conversions</th>
              <th>Progress</th>
              <th>Confidence</th>
              <th>Recommendation</th>
              <th>Top Model</th>
              <th>Top Win Prob</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rows" :key="item.experimentId">
              <td>
                <NuxtLink :to="`/experiments/${item.experimentId}`">{{ item.name }}</NuxtLink>
              </td>
              <td>{{ item.status }}</td>
              <td>{{ item.exposures }}</td>
              <td>{{ item.conversions }}</td>
              <td>{{ pct(item.sampleProgress) }}</td>
              <td>{{ pct(item.confidence) }}</td>
              <td>{{ item.recommendation }}</td>
              <td>{{ item.topModel }}</td>
              <td>{{ pct(item.topWinProb) }}</td>
            </tr>
            <tr v-if="rows.length === 0">
              <td colspan="9">No running experiments yet.</td>
            </tr>
          </tbody>
        </table>
      </article>
      <article class="card" v-if="selectedReport">
        <h3 class="section-title">Model Win Probabilities ({{ selectedName }})</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Exposures</th>
              <th>Conversions</th>
              <th>Expected Rate</th>
              <th>Win Probability</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="variant in selectedReport.bandit_state" :key="variant.variant_id">
              <td>{{ variant.variant_name }}</td>
              <td>{{ variant.exposures }}</td>
              <td>{{ variant.conversions }}</td>
              <td>{{ pct(variant.expected_rate) }}</td>
              <td>{{ pct(variant.win_probability) }}</td>
            </tr>
          </tbody>
        </table>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import type { CondensedPerformance, ExperimentReport } from '~/types'

interface ReportRow {
  experimentId: string
  name: string
  status: string
  exposures: number
  conversions: number
  sampleProgress: number
  confidence: number
  recommendation: string
  topModel: string
  topWinProb: number
}

const { listRunningExperiments, getExperimentReport } = useApi()

const rows = ref<ReportRow[]>([])
const reportsByExperimentId = ref<Record<string, ExperimentReport>>({})
const pending = ref(true)
const errorMessage = ref('')

const selectedReport = computed(() => {
  const first = rows.value[0]
  return first ? reportsByExperimentId.value[first.experimentId] ?? null : null
})

const selectedName = computed(() => rows.value[0]?.name ?? 'Experiment')

const pct = (value: number) => `${(value * 100).toFixed(2)}%`

const normalizeStatus = (status: string) => status.toUpperCase()

const load = async () => {
  pending.value = true
  errorMessage.value = ''
  try {
    const running = await listRunningExperiments()
    const reportEntries = await Promise.all(
      running.map(async (item: CondensedPerformance) => {
        const report = await getExperimentReport(item.experiment_id)
        return [item.experiment_id, report] as const
      })
    )
    reportsByExperimentId.value = Object.fromEntries(reportEntries)
    rows.value = running.map((item) => {
      const report = reportsByExperimentId.value[item.experiment_id]
      const top = [...(report?.bandit_state ?? [])].sort((a, b) => b.win_probability - a.win_probability)[0]
      return {
        experimentId: item.experiment_id,
        name: item.name,
        status: normalizeStatus(String(item.status)),
        exposures: item.exposures,
        conversions: item.conversions,
        sampleProgress: item.sample_progress,
        confidence: report?.confidence ?? item.confidence,
        recommendation: report?.recommendation ?? 'continue_collecting',
        topModel: top?.variant_name ?? '-',
        topWinProb: top?.win_probability ?? 0,
      }
    })
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    pending.value = false
  }
}

onMounted(load)
</script>
