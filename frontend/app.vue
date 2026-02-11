<template>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <span class="brand-mark">L</span>
        <div>
          <p class="brand-title">Litmus</p>
          <p class="brand-sub">Experiment Platform</p>
        </div>
      </div>

      <nav class="menu">
        <NuxtLink to="/" :class="linkClass('/')">Overview</NuxtLink>
        <NuxtLink to="/experiments" :class="linkClass('/experiments')">Experiments</NuxtLink>
        <NuxtLink to="/metrics" :class="linkClass('/metrics')">Metrics</NuxtLink>
        <NuxtLink to="/reports" :class="linkClass('/reports')">Reports</NuxtLink>
      </nav>
    </aside>

    <main class="panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">Self-Serve Experimentation</p>
          <h1 class="title">Global DS/ML Platform</h1>
        </div>
      </header>
      <NuxtPage />
    </main>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()

const linkClass = (basePath: string) => {
  const active = route.path === basePath || route.path.startsWith(`${basePath}/`)
  return active ? 'menu-link menu-link-active' : 'menu-link'
}
</script>
