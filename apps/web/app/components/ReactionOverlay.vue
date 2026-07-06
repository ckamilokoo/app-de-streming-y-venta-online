<script setup lang="ts">
import { REACTIONS } from '~/types'

defineProps<{
  reactions: { id: number; emoji: string }[]
  canReact: boolean
}>()
const emit = defineEmits<{ react: [emoji: string] }>()

// Posición horizontal pseudo-aleatoria estable por id
function xPos(id: number) {
  return 8 + ((id * 37) % 70)
}
</script>

<template>
  <div class="overlay">
    <span
      v-for="r in reactions"
      :key="r.id"
      class="float"
      :style="{ left: xPos(r.id) + '%', animationDelay: (r.id % 3) * 60 + 'ms' }"
    >{{ r.emoji }}</span>
    <div v-if="canReact" class="bar">
      <button
        v-for="e in REACTIONS"
        :key="e"
        class="ghost react-btn"
        @click="emit('react', e)"
      >{{ e }}</button>
    </div>
  </div>
</template>

<style scoped>
.overlay { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.float {
  position: absolute;
  bottom: 3.6rem;
  font-size: 1.7rem;
  animation: float-up 2.5s ease-out forwards;
}
.bar {
  position: absolute;
  bottom: .7rem;
  right: .7rem;
  display: flex;
  gap: .2rem;
  pointer-events: auto;
  background: rgba(13, 15, 20, .55);
  backdrop-filter: blur(6px);
  border-radius: 999px;
  padding: .15rem .3rem;
}
.react-btn {
  border: none;
  padding: .25rem .35rem;
  font-size: 1.15rem;
  border-radius: 999px;
}
.react-btn:hover { background: rgba(255, 255, 255, .12); transform: scale(1.15); }
</style>
