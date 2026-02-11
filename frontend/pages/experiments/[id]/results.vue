<template>
  <section class="page">
    <div class="page-head">
      <h2 class="page-title">Results Dashboard</h2>
      <NuxtLink :to="`/experiments/${experimentId}`" class="button">Back to Detail</NuxtLink>
    </div>

    <article class="card form-grid">
      <label>
        <span>Bucket Interval</span>
        <select v-model="interval" @change="load">
          <option value="hour">Hour</option>
          <option value="minute">Minute</option>
        </select>
      </label>
      <label>
        <span>Auto refresh</span>
        <select v-model="autoRefresh">
          <option :value="true">On</option>
          <option :value="false">Off</option>
        </select>
      </label>
    </article>

    <article class="card" v-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>

    <template v-if="results">
      <article class="card">
        <h3 class="section-title">Exposure Totals</h3>
        <div class="bar-group">
          <div class="bar-row" v-for="(count, key) in results.exposure_totals" :key="key">
            <div class="bar-meta">
              <strong>{{ key }}</strong>
              <span>{{ count }}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${barWidth(count)}%` }" />
            </div>
          </div>
        </div>
      </article>

      <article class="card">
        <h3 class="section-title">Metric Summaries</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Variant</th>
              <th>Metric</th>
              <th>Count</th>
              <th>Mean</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="summary in results.metric_summaries" :key="`${summary.variant_key}-${summary.metric_name}`">
              <td>{{ summary.variant_name }}</td>
              <td>{{ summary.metric_name }}</td>
              <td>{{ summary.count }}</td>
              <td>{{ summary.mean.toFixed(4) }}</td>
            </tr>
            <tr v-if="results.metric_summaries.length === 0">
              <td colspan="4">No metric events yet.</td>
            </tr>
          </tbody>
        </table>
      </article>

      <article class="card">
        <h3 class="section-title">Lift Estimates</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Variant</th>
              <th>Control Rate</th>
              <th>Treatment Rate</th>
              <th>Absolute Lift</th>
              <th>CI</th>
              <th>p-value</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lift in results.lift_estimates" :key="lift.variant_key">
              <td>{{ lift.variant_name }}</td>
              <td>{{ lift.control_rate.toFixed(4) }}</td>
              <td>{{ lift.treatment_rate.toFixed(4) }}</td>
              <td>{{ lift.absolute_lift.toFixed(4) }}</td>
              <td>[{{ lift.ci_lower.toFixed(4) }}, {{ lift.ci_upper.toFixed(4) }}]</td>
              <td>{{ lift.p_value.toFixed(4) }}</td>
            </tr>
            <tr v-if="results.lift_estimates.length === 0">
              <td colspan="6">Lift appears once control and treatment have exposure data.</td>
            </tr>
          </tbody>
        </table>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import type { ExperimentResultsResponse } from '~/types'

const route = useRoute()
const experimentId = route.params.id as string

const { getResults } = useApi()

const interval = ref<'minute' | 'hour'>('hour')
const autoRefresh = ref(true)
const results = ref<ExperimentResultsResponse | null>(null)
const errorMessage = ref('')
let pollHandle: ReturnType<typeof setInterval> | null = null

const load = async () => {
  errorMessage.value = ''
  try {
    results.value = await getResults(experimentId, interval.value)
  } catch (error) {
    errorMessage.value = (error as Error).message
  }
}

const barWidth = (value: number) => {
  if (!results.value) return 0
  const max = Math.max(...Object.values(results.value.exposure_totals), 1)
  return Math.round((value / max) * 100)
}

onMounted(async () => {
  await load()
  pollHandle = setInterval(async () => {
    if (!autoRefresh.value) return
    await load()
  }, 15000)
})

onBeforeUnmount(() => {
  if (pollHandle) clearInterval(pollHandle)
})
</script>
