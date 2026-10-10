<script setup lang="ts">
/** Dark opening band shared by inner marketing pages (the header sits on it). */
withDefaults(defineProps<{ eyebrow?: string; title: string; subtitle?: string; compact?: boolean }>(), { compact: false })
</script>

<template>
  <section class="relative overflow-hidden bg-night-950 pt-[72px] text-white">
    <AuroraBackground />
    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :class="compact ? 'pt-10 pb-14' : 'pt-16 pb-20 lg:pt-20 lg:pb-24'">
      <div class="mx-auto max-w-3xl text-center">
        <p
          v-if="eyebrow"
          class="rise glass-dark mb-5 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-bold tracking-[0.14em] text-lagoon uppercase rtl:tracking-normal"
        >
          {{ eyebrow }}
        </p>
        <h1 style="--d: 50ms"
          class="rise text-4xl leading-[1.1] font-extrabold sm:text-5xl lg:text-6xl"
        >
          <slot name="title">{{ title }}</slot>
        </h1>
        <p style="--d: 120ms"
          v-if="subtitle"
          class="rise mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-white/70"
        >
          {{ subtitle }}
        </p>
        <div v-if="$slots.default" class="mt-8"><slot /></div>
      </div>
    </div>
    <svg class="relative block w-full text-bg" viewBox="0 0 1440 40" preserveAspectRatio="none" aria-hidden="true">
      <path fill="currentColor" d="M0 40h1440V0c-240 26-480 40-720 40S240 26 0 0z" />
    </svg>
  </section>
</template>
