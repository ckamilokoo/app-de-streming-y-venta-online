<script setup lang="ts">
// Con Clerk real este widget se reemplaza por <UserButton /> + <SignInButton />.
const { user, logout } = useAuth()
const { show } = useAuthModal()
</script>

<template>
  <button v-if="!user" class="primary" @click="show()">Iniciar sesión</button>
  <div v-else class="row">
    <span class="badge" :class="{ streamer: user.role === 'streamer' }">
      {{ user.role === 'streamer' ? '🎥 streamer' : '🛍️ comprador' }}
    </span>
    <strong>{{ user.name }}</strong>
    <button class="ghost" @click="logout">Salir</button>
  </div>
</template>
