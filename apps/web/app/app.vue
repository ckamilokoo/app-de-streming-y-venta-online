<script setup lang="ts">
const { user, isStreamer } = useAuth()
</script>

<template>
  <div class="shell">
    <header class="site-header">
      <div class="container row header-inner">
        <NuxtLink to="/" class="logo">🔴 LiveCommerce</NuxtLink>
        <nav class="row">
          <NuxtLink to="/">Lobby</NuxtLink>
          <NuxtLink v-if="user" to="/orders">Mis compras</NuxtLink>
          <NuxtLink v-if="isStreamer" to="/studio">Studio</NuxtLink>
        </nav>
        <div class="spacer" />
        <DevAuth />
      </div>
    </header>

    <main>
      <NuxtPage :key="user?.id ?? 'anon'" />
    </main>

    <footer class="site-footer">
      <div class="container">
        <strong>🔴 LiveCommerce</strong> — live shopping: streams en vivo con chat,
        productos destacados y compra en tiempo real antes de que se agote el stock.
        <span class="muted">MVP demo · pagos simulados · video Cloudflare Stream en fase 0.</span>
      </div>
    </footer>

    <AuthModal />
  </div>
</template>

<style scoped>
.shell { min-height: 100vh; display: flex; flex-direction: column; }
main { flex: 1; }

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

.site-footer {
  border-top: 1px solid var(--border);
  margin-top: 2rem;
  padding: 1rem 0 1.4rem;
  font-size: .8rem;
  color: var(--muted);
}
.site-footer strong { color: var(--text); }
</style>
