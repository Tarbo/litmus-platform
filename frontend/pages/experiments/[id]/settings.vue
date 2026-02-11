<template>
  <section class="page">
    <div class="page-head">
      <h2 class="page-title">Experiment Settings</h2>
      <NuxtLink :to="`/experiments/${experimentId}`" class="button">Back to Detail</NuxtLink>
    </div>

    <article class="card" v-if="pending">
      <p>Loading settings...</p>
    </article>

    <article class="card" v-else-if="errorMessage">
      <p class="error">{{ errorMessage }}</p>
    </article>

    <article class="card" v-else-if="experiment">
      <form class="form-grid" @submit.prevent="save">
        <label>
          <span>Name</span>
          <input v-model="name" required minlength="3" />
        </label>
        <label>
          <span>Owner Team</span>
          <input v-model="ownerTeam" required />
        </label>
        <label>
          <span>Ramp %</span>
          <input v-model.number="rampPct" type="number" min="0" max="100" />
        </label>
        <label class="full">
          <span>Description</span>
          <textarea v-model="description" rows="3" required minlength="5" />
        </label>
        <label class="full">
          <span>Tags (comma-separated)</span>
          <input v-model="tagsInput" />
        </label>
        <label class="full">
          <span>Targeting JSON</span>
          <textarea v-model="targetingInput" rows="5" />
        </label>

        <p class="error" v-if="saveError">{{ saveError }}</p>
        <p class="ok" v-if="saveSuccess">{{ saveSuccess }}</p>

        <div class="actions full">
          <button type="submit" class="button button-primary" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { Experiment } from '~/types'

const route = useRoute()
const experimentId = route.params.id as string
const { getExperiment, patchExperiment } = useApi()

const experiment = ref<Experiment | null>(null)
const pending = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const saveError = ref('')
const saveSuccess = ref('')

const name = ref('')
const description = ref('')
const ownerTeam = ref('')
const rampPct = ref(0)
const tagsInput = ref('')
const targetingInput = ref('{}')

const hydrate = (value: Experiment) => {
  name.value = value.name
  description.value = value.description
  ownerTeam.value = value.owner_team
  rampPct.value = value.ramp_pct
  tagsInput.value = value.tags.join(', ')
  targetingInput.value = JSON.stringify(value.targeting || {}, null, 2)
}

const load = async () => {
  experiment.value = await getExperiment(experimentId)
  hydrate(experiment.value)
}

const parseTargeting = () => {
  try {
    const parsed = JSON.parse(targetingInput.value)
    return typeof parsed === 'object' && parsed !== null ? parsed : {}
  } catch {
    return {}
  }
}

const save = async () => {
  saveError.value = ''
  saveSuccess.value = ''
  saving.value = true
  try {
    await patchExperiment(experimentId, {
      name: name.value,
      description: description.value,
      owner_team: ownerTeam.value,
      ramp_pct: rampPct.value,
      tags: tagsInput.value
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
      targeting: parseTargeting(),
    })
    await load()
    saveSuccess.value = 'Experiment settings updated.'
  } catch (error) {
    saveError.value = (error as Error).message
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    await load()
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    pending.value = false
  }
})
</script>
