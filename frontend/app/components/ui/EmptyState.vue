<script setup lang="ts">
defineProps<{ icon?: string; title: string; text?: string }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center px-6 py-14 text-center">
    <div class="relative mb-5 grid size-16 place-items-center rounded-2xl bg-sea/10 text-sea">
      <span class="animate-ping-slow absolute inset-0 rounded-2xl bg-sea/10" />
      <AppIcon :name="icon || 'inbox'" :size="28" />
    </div>
    <h3 class="text-lg font-bold">{{ title }}</h3>
    <p v-if="text" class="mt-2 max-w-sm text-sm text-muted">{{ text }}</p>
    <div v-if="$slots.default" class="mt-6"><slot /></div>
  </div>
</template>
