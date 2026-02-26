export default defineNuxtConfig({
  css: ['~/assets/css/main.css'],
  devtools: { enabled: false },
  runtimeConfig: {
    apiBaseInternal: process.env.NUXT_API_BASE_INTERNAL ?? process.env.NUXT_PUBLIC_API_BASE ?? 'http://localhost:8000/api/v1',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE ?? 'http://localhost:8000/api/v1',
    },
  },
})
