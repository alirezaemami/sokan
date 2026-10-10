<script setup lang="ts">
withDefaults(defineProps<{ icon: string; label: string; value: string | number; hint?: string; tone?: 'sea' | 'success' | 'buoy' | 'warning' | 'tide' }>(), { tone: 'sea' })
const tones = {
  sea: 'bg-sea/10 text-sea',
  success: 'bg-success/12 text-success',
  buoy: 'bg-buoy/12 text-buoy',
  warning: 'bg-warning/15 text-warning',
  tide: 'bg-tide/15 text-sea dark:text-tide',
}
</script>

<template>
  <div class="card p-5">
    <div class="flex items-center justify-between">
      <span class="grid size-10 place-items-center rounded-xl" :class="tones[tone]"><AppIcon :name="icon" :size="19" /></span>
    </div>
    <p class="font-display mt-4 text-3xl tabular-nums sm:text-4xl">{{ value }}</p>
    <p class="mt-0.5 text-sm text-muted">{{ label }}</p>
    <p v-if="hint" class="mt-1 text-xs text-faint">{{ hint }}</p>
  </div>
</template>
