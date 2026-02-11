<template>
  <section class="page">
    <div class="page-head">
      <h2 class="page-title">Create Experiment</h2>
      <NuxtLink to="/experiments" class="button">Back</NuxtLink>
    </div>

    <article class="card">
      <form class="form-grid" @submit.prevent="submit">
        <label>
          <span>Name</span>
          <input v-model="form.name" required minlength="3" />
        </label>
        <label>
          <span>Owner Team</span>
          <input v-model="form.owner_team" required />
        </label>
        <label>
          <span>Created By</span>
          <input v-model="form.created_by" required />
        </label>
        <label>
          <span>Unit Type</span>
          <input v-model="form.unit_type" required />
        </label>
        <label class="full">
          <span>Description</span>
          <textarea v-model="form.description" rows="3" required minlength="5" />
        </label>
        <label class="full">
          <span>Tags (comma-separated)</span>
          <input v-model="tagsInput" placeholder="pricing, checkout, model-v4" />
        </label>
        <label>
          <span>Ramp %</span>
          <input v-model.number="form.ramp_pct" type="number" min="0" max="100" />
        </label>
        <label class="full">
          <span>Targeting JSON</span>
          <textarea v-model="targetingInput" rows="4" />
        </label>

        <section class="full">
          <div class="inline-head">
            <h3>Variants</h3>
            <button type="button" class="button" @click="addVariant">Add variant</button>
          </div>
          <div class="variant-grid">
            <article class="variant-card" v-for="(variant, idx) in form.variants" :key="idx">
              <label>
                <span>Key</span>
                <input v-model="variant.key" required />
              </label>
              <label>
                <span>Name</span>
                <input v-model="variant.name" required />
              </label>
              <label>
                <span>Weight</span>
                <input v-model.number="variant.weight" type="number" min="0" max="1" step="0.01" required />
              </label>
              <label>
                <span>Config JSON</span>
                <textarea v-model="variant.configText" rows="4" />
              </label>
              <button type="button" class="button button-danger" @click="removeVariant(idx)">Remove</button>
            </article>
          </div>
        </section>

        <p class="error" v-if="errorMessage">{{ errorMessage }}</p>
        <p class="ok" v-if="successMessage">{{ successMessage }}</p>

        <div class="actions full">
          <button type="submit" class="button button-primary" :disabled="submitting">
            {{ submitting ? 'Creating...' : 'Create Experiment' }}
          </button>
        </div>
      </form>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { ExperimentCreatePayload } from '~/types'

interface VariantDraft {
  key: string
  name: string
  weight: number
  configText: string
}

const router = useRouter()
const { createExperiment } = useApi()

const form = ref({
  name: '',
  description: '',
  owner_team: 'growth-ds',
  created_by: 'team.member',
  unit_type: 'user_id',
  ramp_pct: 10,
  variants: [
    { key: 'control', name: 'Control', weight: 0.5, configText: '{}' },
    { key: 'treatment', name: 'Treatment', weight: 0.5, configText: '{}' },
  ] as VariantDraft[],
})

const tagsInput = ref('')
const targetingInput = ref('{}')
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const addVariant = () => {
  form.value.variants.push({ key: '', name: '', weight: 0.0, configText: '{}' })
}

const removeVariant = (index: number) => {
  if (form.value.variants.length <= 2) return
  form.value.variants.splice(index, 1)
}

const safeParseJson = (input: string, fallback: Record<string, unknown> = {}) => {
  try {
    const parsed = JSON.parse(input)
    return typeof parsed === 'object' && parsed !== null ? parsed : fallback
  } catch {
    return fallback
  }
}

const submit = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  submitting.value = true

  const payload: ExperimentCreatePayload = {
    name: form.value.name,
    description: form.value.description,
    owner_team: form.value.owner_team,
    created_by: form.value.created_by,
    unit_type: form.value.unit_type,
    ramp_pct: form.value.ramp_pct,
    tags: tagsInput.value
      .split(',')
      .map((v) => v.trim())
      .filter(Boolean),
    targeting: safeParseJson(targetingInput.value, {}),
    variants: form.value.variants.map((variant) => ({
      key: variant.key,
      name: variant.name,
      weight: variant.weight,
      config_json: safeParseJson(variant.configText, {}),
    })),
  }

  try {
    const created = await createExperiment(payload)
    successMessage.value = `Experiment ${created.name} created.`
    await router.push(`/experiments/${created.id}`)
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    submitting.value = false
  }
}
</script>
