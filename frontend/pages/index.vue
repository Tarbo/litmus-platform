<template>
  <section class="page">
    <div class="page-head">
      <h2 class="page-title">Platform Overview</h2>
      <NuxtLink to="/experiments" class="button button-primary">Open Experiments</NuxtLink>
    </div>

    <article class="card" v-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>

    <div class="card-grid" v-else>
      <article class="card">
        <p class="label">Total Experiments</p>
        <p class="stat">{{ experiments.length }}</p>
      </article>
      <article class="card">
        <p class="label">Running</p>
        <p class="stat">{{ summary.RUNNING }}</p>
      </article>
      <article class="card">
        <p class="label">Draft</p>
        <p class="stat">{{ summary.DRAFT }}</p>
      </article>
      <article class="card">
        <p class="label">Paused / Stopped</p>
        <p class="stat">{{ summary.PAUSED + summary.STOPPED }}</p>
      </article>
    </div>

    <article class="card">
      <h3 class="section-title">Recent Experiments</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Owner Team</th>
            <th>Ramp</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exp in recent" :key="exp.id">
            <td>{{ exp.name }}</td>
            <td><span class="badge" :class="statusClass(exp.status)">{{ normalizeStatus(exp.status) }}</span></td>
            <td>{{ exp.owner_team }}</td>
            <td>{{ exp.ramp_pct }}%</td>
            <td><NuxtLink :to="`/experiments/${exp.id}`" class="button">Open</NuxtLink></td>
          </tr>
          <tr v-if="recent.length === 0">
            <td colspan="5">No experiments yet.</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { Experiment } from '~/types'

const { listExperiments } = useApi()

const experiments = ref<Experiment[]>([])
const errorMessage = ref('')

const normalizeStatus = (status: string) => status.toUpperCase()
const statusClass = (status: string) => `status-${normalizeStatus(status).toLowerCase()}`

const summary = computed(() => {
  const base = { DRAFT: 0, RUNNING: 0, PAUSED: 0, STOPPED: 0 }
  for (const experiment of experiments.value) {
    const status = normalizeStatus(experiment.status) as keyof typeof base
    if (base[status] !== undefined) {
      base[status] += 1
    }
  }
  return base
})

const recent = computed(() => experiments.value.slice(0, 8))

onMounted(async () => {
  try {
    experiments.value = await listExperiments()
  } catch (error) {
    errorMessage.value = (error as Error).message
  }
})
</script>
