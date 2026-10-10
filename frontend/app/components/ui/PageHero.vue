<script setup lang="ts">
/** Opening band for inner pages: sea paper, contours, display headline. */
withDefaults(defineProps<{ eyebrow?: string; title: string; subtitle?: string; compact?: boolean }>(), { compact: false })
</script>

<template>
  <section class="relative overflow-hidden border-b border-line pt-[72px]">
    <ChartBackground :density="12" />
    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8" :class="compact ? 'pt-10 pb-12' : 'pt-14 pb-16 lg:pt-20 lg:pb-20'">
      <div class="mx-auto max-w-3xl text-center">
        <p v-if="eyebrow" class="rise chart-label mb-4 inline-flex items-center gap-2 text-sea">
          <span class="size-1.5 rounded-full bg-buoy" /> {{ eyebrow }}
        </p>
        <h1 class="rise font-display text-4xl leading-[1.06] text-ink sm:text-5xl lg:text-6xl" style="--d: 50ms">
          <slot name="title">{{ title }}</slot>
        </h1>
        <p v-if="subtitle" class="rise mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted" style="--d: 120ms">
          {{ subtitle }}
        </p>
        <div v-if="$slots.default" class="rise mt-8" style="--d: 180ms"><slot /></div>
      </div>
    </div>
  </section>
</template>
