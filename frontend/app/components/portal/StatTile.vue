<script setup lang="ts">
withDefaults(defineProps<{ icon: string; label: string; value: string | number; hint?: string; tone?: 'brand' | 'success' | 'coral' | 'warning' | 'lagoon' }>(), { tone: 'brand' })
const tones = {
  brand: 'bg-brand/10 text-brand',
  success: 'bg-success/12 text-success',
  coral: 'bg-coral/12 text-coral',
  warning: 'bg-warning/15 text-warning',
  lagoon: 'bg-lagoon/15 text-lagoon-deep dark:text-lagoon',
}
</script>

<template>
  <div class="card p-5">
    <div class="flex items-center justify-between">
      <span class="grid size-10 place-items-center rounded-xl" :class="tones[tone]"><AppIcon :name="icon" :size="19" /></span>
    </div>
    <p class="mt-4 text-2xl font-extrabold tracking-tight tabular-nums sm:text-3xl">{{ value }}</p>
    <p class="mt-0.5 text-sm text-muted">{{ label }}</p>
    <p v-if="hint" class="mt-1 text-xs text-faint">{{ hint }}</p>
  </div>
</template>
