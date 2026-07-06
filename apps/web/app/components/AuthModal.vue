<script setup lang="ts">
const { open, preferredRole, hide } = useAuthModal()
const { login } = useAuth()
const router = useRouter()

const role = ref<'buyer' | 'streamer'>('buyer')
const name = ref('')
const nameEl = ref<HTMLInputElement>()

watch(open, (o) => {
  if (o) {
    role.value = preferredRole.value
    nextTick(() => nameEl.value?.focus())
  }
})

function submit() {
  if (!name.value.trim()) return
  login(name.value, role.value)
  hide()
  name.value = ''
  if (role.value === 'streamer') router.push('/studio')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="backdrop" @click.self="hide()">
      <div class="modal">
        <div class="row head">
          <h2>Entrar a LiveCommerce</h2>
          <button class="ghost" @click="hide()">✕</button>
        </div>
        <p class="muted lead">¿Cómo quieres usar la app?</p>

        <div class="roles">
          <button
            type="button"
            class="role-card"
            :class="{ active: role === 'buyer' }"
            @click="role = 'buyer'"
          >
            <span class="icon">🛍️</span>
            <strong>Comprador</strong>
            <span class="desc">Mira streams en vivo, chatea, reacciona y compra antes de que se agote.</span>
          </button>
          <button
            type="button"
            class="role-card"
            :class="{ active: role === 'streamer' }"
            @click="role = 'streamer'"
          >
            <span class="icon">🎥</span>
            <strong>Streamer</strong>
            <span class="desc">Crea tu catálogo, transmite con tu cámara y vende destacando productos en vivo.</span>
          </button>
        </div>

        <form @submit.prevent="submit">
          <label class="muted" for="auth-name">Tu nombre</label>
          <input
            id="auth-name"
            ref="nameEl"
            v-model="name"
            placeholder="Ej: Camilo"
            maxlength="40"
            required
          />
          <button type="submit" class="buy enter" :disabled="!name.trim()">
            Entrar como {{ role === 'buyer' ? 'comprador' : 'streamer' }}
          </button>
        </form>
        <p class="muted note">Demo sin contraseña — el mismo nombre recupera tu cuenta. Login real (Clerk) llega en fase 2.</p>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.backdrop {
  position: fixed; inset: 0; z-index: 60;
  background: rgba(0, 0, 0, .6);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}
.modal {
  width: min(520px, 100%);
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.4rem;
  animation: slide-up .25s ease;
}
.head { justify-content: space-between; }
.head h2 { margin: 0; font-size: 1.25rem; }
.lead { margin: .3rem 0 1rem; }

.roles { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin-bottom: 1.1rem; }
@media (max-width: 480px) { .roles { grid-template-columns: 1fr; } }
.role-card {
  display: flex; flex-direction: column; align-items: flex-start; gap: .3rem;
  text-align: left;
  padding: .9rem;
  border-radius: 12px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: border-color .15s, box-shadow .15s;
}
.role-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent) inset, 0 0 18px rgba(109, 92, 255, .2);
}
.role-card .icon { font-size: 1.6rem; }
.role-card .desc { font-size: .78rem; color: var(--muted); line-height: 1.35; }

form { display: flex; flex-direction: column; gap: .5rem; }
label { font-size: .8rem; }
.enter { padding: .75rem; font-size: 1rem; border-radius: 10px; margin-top: .3rem; }
.note { font-size: .72rem; margin: .8rem 0 0; }
</style>
