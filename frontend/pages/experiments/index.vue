<template>
  <section class="page">
    <div class="page-head">
      <h2 class="page-title">Experiments</h2>
      <NuxtLink to="/experiments/new" class="button button-primary">New experiment</NuxtLink>
    </div>

    <article class="card form-grid filters-row">
      <label>
        <span>Status</span>
        <select v-model="statusFilter">
          <option value="all">All</option>
          <option value="DRAFT">Draft</option>
          <option value="RUNNING">Running</option>
          <option value="PAUSED">Paused</option>
          <option value="STOPPED">Stopped</option>
        </select>
      </label>
      <label>
        <span>Search</span>
        <input v-model="search" placeholder="Name, owner team, tag" />
      </label>
    </article>

    <article class="card" v-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>

    <article class="card" v-if="pending">
      <p>Loading experiments...</p>
    </article>

    <article class="card" v-else>
      <table class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Owner Team</th>
            <th>Status</th>
            <th>Ramp</th>
            <th>Variants</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exp in filteredExperiments" :key="exp.id">
            <td>{{ exp.name }}</td>
            <td>{{ exp.owner_team }}</td>
            <td>
              <span class="badge" :class="statusClass(exp.status)">{{ normalizeStatus(exp.status) }}</span>
            </td>
            <td>{{ exp.ramp_pct }}%</td>
            <td>{{ exp.variants.length }}</td>
            <td>
              <NuxtLink :to="`/experiments/${exp.id}`" class="button">Open</NuxtLink>
            </td>
          </tr>
          <tr v-if="filteredExperiments.length === 0">
            <td colspan="6">No experiments match current filters.</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { Experiment } from '~/types'

const { listExperiments } = useApi()

const statusFilter = ref('all')
const search = ref('')
const errorMessage = ref('')
const pending = ref(true)
const experiments = ref<Experiment[]>([])

const normalizeStatus = (status: string) => status.toUpperCase()
const statusClass = (status: string) => `status-${normalizeStatus(status).toLowerCase()}`

const filteredExperiments = computed(() => {
  const query = search.value.trim().toLowerCase()
  return experiments.value.filter((exp) => {
    const statusMatch = statusFilter.value === 'all' || normalizeStatus(exp.status) === statusFilter.value
    const text = `${exp.name} ${exp.owner_team} ${exp.tags.join(' ')}`.toLowerCase()
    const textMatch = query.length === 0 || text.includes(query)
    return statusMatch && textMatch
  })
})

onMounted(async () => {
  try {
    experiments.value = await listExperiments()
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    pending.value = false
  }
})
</script>
