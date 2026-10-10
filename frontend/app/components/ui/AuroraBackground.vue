<script setup lang="ts">
/**
 * Ambient background: drifting colour blooms over a faint grid and grain.
 * Pure CSS — nothing on the main thread — and frozen under reduced motion.
 */
withDefaults(defineProps<{ grid?: boolean }>(), { grid: true })
</script>

<template>
  <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    <div v-if="grid" class="grid-fade absolute inset-0" />
    <div
      class="animate-aurora absolute -top-[30%] start-[-10%] aspect-square w-[75vw] max-w-[900px] rounded-full opacity-50 blur-[120px]"
      style="background: radial-gradient(circle, rgb(91 92 246 / 0.7), transparent 65%)"
    />
    <div
      class="animate-aurora absolute -top-[10%] end-[-15%] aspect-square w-[60vw] max-w-[760px] rounded-full opacity-40 blur-[120px]"
      style="animation-delay: -8s; background: radial-gradient(circle, rgb(34 211 238 / 0.6), transparent 65%)"
    />
    <div
      class="animate-aurora absolute bottom-[-35%] start-[25%] aspect-square w-[50vw] max-w-[640px] rounded-full opacity-25 blur-[120px]"
      style="animation-delay: -15s; background: radial-gradient(circle, rgb(255 107 74 / 0.6), transparent 65%)"
    />
    <div
      class="absolute inset-0 opacity-[0.05] mix-blend-overlay"
      style="background-image: url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22160%22 height=%22160%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22/></filter><rect width=%22160%22 height=%22160%22 filter=%22url(%23n)%22/></svg>')"
    />
  </div>
</template>
