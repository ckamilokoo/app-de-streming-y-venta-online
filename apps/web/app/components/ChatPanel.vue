<script setup lang="ts">
import type { ChatMsg } from '~/types'

const props = defineProps<{
  messages: ChatMsg[]
  connected: boolean
  canWrite: boolean
  placeholder?: string
}>()
const emit = defineEmits<{ send: [text: string]; login: [] }>()

const input = ref('')
const listEl = ref<HTMLElement>()

function submit() {
  if (!input.value.trim()) return
  emit('send', input.value)
  input.value = ''
}

// Autoscroll al fondo con cada mensaje nuevo
watch(() => props.messages.length, async () => {
  await nextTick()
  listEl.value?.scrollTo({ top: listEl.value.scrollHeight })
})

function time(ts: number) {
  return new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="chat panel">
    <div class="row head">
      <h3 style="margin:0">Chat</h3>
      <span class="dot" :class="{ on: connected }" :title="connected ? 'Conectado' : 'Reconectando…'" />
    </div>
    <div ref="listEl" class="messages">
      <p v-for="(m, i) in messages" :key="i" class="msg">
        <span class="time">{{ time(m.ts) }}</span>
        <strong :class="{ isStreamer: m.role === 'streamer' }">
          <span v-if="m.role === 'streamer'" class="badge streamer">STREAMER</span>
          {{ m.name }}:
        </strong>
        {{ m.text }}
      </p>
      <p v-if="!messages.length" class="muted">Sé el primero en escribir…</p>
    </div>
    <form v-if="canWrite" class="row" @submit.prevent="submit">
      <input
        v-model="input"
        :placeholder="placeholder ?? 'Escribe un mensaje'"
        maxlength="280"
        style="flex:1"
      />
      <button type="submit" :disabled="!connected">➤</button>
    </form>
    <button v-else class="primary" @click="emit('login')">Inicia sesión para chatear</button>
  </div>
</template>

<style scoped>
.chat { display: flex; flex-direction: column; min-height: 0; }
.head { justify-content: space-between; margin-bottom: .5rem; }
.dot {
  width: 9px; height: 9px; border-radius: 50%;
  background: var(--warn);
}
.dot.on { background: var(--ok); }
.messages { flex: 1; overflow-y: auto; margin-bottom: .6rem; min-height: 180px; }
.msg { margin: .3rem 0; word-break: break-word; font-size: .9rem; }
.time { color: var(--muted); font-size: .7rem; margin-right: .35rem; }
.isStreamer { color: #ff9aa5; }
.badge.streamer { font-size: .58rem; padding: .05rem .4rem; margin-right: .25rem; }
</style>
