<script setup lang="ts">
// Widget de login mock (dev). Con Clerk real se reemplaza por <SignInButton />.
const { user, login, logout } = useAuth()
const name = ref('')
const role = ref<'buyer' | 'streamer'>('buyer')

function submit() {
  if (name.value.trim()) login(name.value, role.value)
}
</script>

<template>
  <form v-if="!user" class="row" @submit.prevent="submit">
    <input v-model="name" placeholder="Tu nombre" size="12" required />
    <select v-model="role">
      <option value="buyer">Comprador</option>
      <option value="streamer">Streamer</option>
    </select>
    <button type="submit" class="primary">Entrar</button>
  </form>
  <div v-else class="row">
    <span class="badge" :class="{ ok: user.role === 'streamer' }">{{ user.role }}</span>
    <strong>{{ user.name }}</strong>
    <button @click="logout">Salir</button>
  </div>
</template>
