import type { Experiment, ExperimentCreatePayload, ExperimentResultsResponse } from '~/types'

export const useApi = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const req = async <T>(path: string, options?: Record<string, unknown>): Promise<T> => {
    try {
      return await $fetch<T>(`${apiBase}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options?.headers as Record<string, string> | undefined),
        },
      })
    } catch (error) {
      const err = error as { data?: { detail?: string }; message?: string }
      const detail = err?.data?.detail || err?.message || 'API request failed'
      throw new Error(detail)
    }
  }

  return {
    listExperiments: () => req<Experiment[]>('/experiments'),
    getExperiment: (id: string) => req<Experiment>(`/experiments/${id}`),
    createExperiment: (payload: ExperimentCreatePayload) =>
      req<Experiment>('/experiments', { method: 'POST', body: payload }),
    patchExperiment: (id: string, payload: Partial<ExperimentCreatePayload>) =>
      req<Experiment>(`/experiments/${id}`, { method: 'PATCH', body: payload }),
    launchExperiment: (id: string, rampPct?: number) =>
      req<Experiment>(`/experiments/${id}/launch`, {
        method: 'POST',
        body: rampPct === undefined ? {} : { ramp_pct: rampPct },
      }),
    pauseExperiment: (id: string) => req<Experiment>(`/experiments/${id}/pause`, { method: 'POST', body: {} }),
    stopExperiment: (id: string) => req<Experiment>(`/experiments/${id}/stop`, { method: 'POST', body: {} }),
    getResults: (id: string, interval: 'minute' | 'hour' = 'hour') =>
      req<ExperimentResultsResponse>(`/results/${id}?interval=${interval}`),
  }
}
