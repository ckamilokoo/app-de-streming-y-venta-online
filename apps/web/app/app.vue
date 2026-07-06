<script setup lang="ts">
const { user, isStreamer } = useAuth()
</script>

<template>
  <div>
    <header class="site-header">
      <div class="container row header-inner">
        <NuxtLink to="/" class="logo">🔴 LiveCommerce</NuxtLink>
        <nav class="row">
          <NuxtLink to="/">Lobby</NuxtLink>
          <NuxtLink v-if="isStreamer" to="/studio">Studio</NuxtLink>
        </nav>
        <div class="spacer" />
        <DevAuth />
      </div>
    </header>
    <NuxtPage :key="user?.id ?? 'anon'" />
  </div>
</template>

<style scoped>
.site-header {
  border-bottom: 1px solid var(--border);
  background: var(--panel);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-inner { padding-top: .7rem; padding-bottom: .7rem; }
.logo { font-weight: 700; font-size: 1.05rem; }
nav a { color: var(--muted); padding: .3rem .5rem; border-radius: 6px; }
nav a.router-link-active { color: var(--text); }
.spacer { flex: 1; }
</style>
