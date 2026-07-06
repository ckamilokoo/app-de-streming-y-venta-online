<script setup lang="ts">
defineProps<{ label: string; value: string; icon?: string }>()
</script>

<template>
  <div class="stat panel">
    <span v-if="icon" class="icon">{{ icon }}</span>
    <div>
      <div class="value">{{ value }}</div>
      <div class="label muted">{{ label }}</div>
    </div>
  </div>
</template>

<style scoped>
.stat { display: flex; align-items: center; gap: .8rem; padding: .9rem 1.1rem; }
.icon { font-size: 1.5rem; }
.value { font-size: 1.35rem; font-weight: 750; line-height: 1.1; }
.label { font-size: .78rem; }
</style>
