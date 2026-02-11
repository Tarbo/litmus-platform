<template>
  <section class="page">
    <div class="page-head">
      <h2 class="page-title">{{ experiment?.name || 'Experiment Detail' }}</h2>
      <div class="actions-inline">
        <NuxtLink :to="`/experiments/${experimentId}/results`" class="button">Results</NuxtLink>
        <NuxtLink :to="`/experiments/${experimentId}/settings`" class="button">Settings</NuxtLink>
      </div>
    </div>

    <article class="card" v-if="pending">
      <p>Loading experiment...</p>
    </article>

    <article class="card" v-else-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>

    <template v-else-if="experiment">
      <section class="card-grid">
        <article class="card">
          <p class="label">Status</p>
          <p class="stat">{{ normalizeStatus(experiment.status) }}</p>
        </article>
        <article class="card">
          <p class="label">Ramp</p>
          <p class="stat">{{ experiment.ramp_pct }}%</p>
        </article>
        <article class="card">
          <p class="label">Owner Team</p>
          <p class="stat stat-small">{{ experiment.owner_team }}</p>
        </article>
      </section>

      <article class="card">
        <p class="label">Description</p>
        <p>{{ experiment.description }}</p>
        <div class="chip-row" v-if="experiment.tags.length > 0">
          <span class="chip" v-for="tag in experiment.tags" :key="tag">{{ tag }}</span>
        </div>
      </article>

      <article class="card form-grid">
        <label>
          <span>Adjust ramp %</span>
          <input v-model.number="rampInput" type="number" min="0" max="100" />
        </label>
        <div class="action-group">
          <button class="button button-primary" :disabled="working" @click="launch">Launch / Update Ramp</button>
          <button class="button" :disabled="working" @click="pause">Pause</button>
          <button class="button button-danger" :disabled="working" @click="stop">Stop</button>
        </div>
      </article>

      <article class="card" v-if="results">
        <h3 class="section-title">Near Real-Time Exposure Totals</h3>
        <div class="card-grid">
          <article class="card" v-for="(count, key) in results.exposure_totals" :key="key">
            <p class="label">{{ key }}</p>
            <p class="stat">{{ count }}</p>
          </article>
        </div>
      </article>

      <p class="ok" v-if="successMessage">{{ successMessage }}</p>
    </template>
  </section>
</template>

<script setup lang="ts">
import type { Experiment, ExperimentResultsResponse } from '~/types'

const route = useRoute()
const experimentId = route.params.id as string

const { getExperiment, launchExperiment, pauseExperiment, stopExperiment, getResults } = useApi()

const experiment = ref<Experiment | null>(null)
const results = ref<ExperimentResultsResponse | null>(null)
const pending = ref(true)
const working = ref(false)
const rampInput = ref(10)
const errorMessage = ref('')
const successMessage = ref('')
let pollHandle: ReturnType<typeof setInterval> | null = null

const normalizeStatus = (status: string) => status.toUpperCase()

const refresh = async () => {
  experiment.value = await getExperiment(experimentId)
  rampInput.value = experiment.value.ramp_pct
}

const refreshResults = async () => {
  results.value = await getResults(experimentId, 'minute')
}

const withAction = async (action: () => Promise<void>, success: string) => {
  working.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await action()
    await refresh()
    await refreshResults()
    successMessage.value = success
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    working.value = false
  }
}

const launch = () => withAction(() => launchExperiment(experimentId, rampInput.value).then(() => undefined), 'Experiment launched/updated.')
const pause = () => withAction(() => pauseExperiment(experimentId).then(() => undefined), 'Experiment paused.')
const stop = () => withAction(() => stopExperiment(experimentId).then(() => undefined), 'Experiment stopped.')

onMounted(async () => {
  try {
    await refresh()
    await refreshResults()
    pollHandle = setInterval(async () => {
      try {
        await refreshResults()
      } catch {
        // Keep polling even if one request fails.
      }
    }, 15000)
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    pending.value = false
  }
})

onBeforeUnmount(() => {
  if (pollHandle) {
    clearInterval(pollHandle)
  }
})
</script>
